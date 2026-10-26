"""
Online metadata lookup via:
  1. Apple iTunes Search API (fast, comprehensive album metadata, no rate-limit)
  2. MusicBrainz text search (artist + title / title only)
  3. AcoustID (audio fingerprint → MusicBrainz recording ID, optional)
"""
import re
import threading
import time
import uuid
import logging
import requests
from pathlib import Path
from typing import Optional
try:
    from organizer.models import SongInfo
    from organizer.filename_parser import clean_artist, clean_title
    from organizer.utils import safe_display
except ImportError:
    from tools.music_organizer.organizer.models import SongInfo
    from tools.music_organizer.organizer.filename_parser import clean_artist, clean_title
    from tools.music_organizer.organizer.utils import safe_display

try:
    from ShazamAPI import Shazam
    HAS_SHAZAM = True
except ImportError:
    HAS_SHAZAM = False

logger = logging.getLogger(__name__)

_SHAZAM_LOCK = threading.Lock()
_LAST_SHAZAM_TIME: float = 0.0
_SHAZAM_MIN_INTERVAL: float = 0.35

if HAS_SHAZAM:
    def _resilient_send_recognize_request(self, sig):
        global _LAST_SHAZAM_TIME
        data = {
            'timezone': 'Europe/London',
            'signature': {
                'uri': sig.encode_to_uri(),
                'samplems': int(sig.number_samples / sig.sample_rate_hz * 1000)
            },
            'timestamp': int(time.time() * 1000),
            'context': {},
            'geolocation': {}
        }

        try:
            from ShazamAPI.const import HEADERS, API_URL
        except ImportError:
            HEADERS = {
                'X-Shazam-Platform': 'IPHONE',
                'X-Shazam-AppVersion': '14.1.0',
                'Accept': '*/*',
                'Accept-Language': 'en',
                'Accept-Encoding': 'gzip, deflate',
                'User-Agent': 'Shazam/3685 CFNetwork/1197 Darwin/20.0.0'
            }
            API_URL = 'https://amp.shazam.com/discovery/v5/en/US/iphone/-/tag/%s/%s?sync=true&webv3=true&sampling=true&connected=&shazamapiversion=v3&sharehub=true&hubv5minorversion=v5.1&hidelb=true&video=v3'

        for attempt in range(3):
            with _SHAZAM_LOCK:
                gap = time.monotonic() - _LAST_SHAZAM_TIME
                if gap < _SHAZAM_MIN_INTERVAL:
                    time.sleep(_SHAZAM_MIN_INTERVAL - gap)
                _LAST_SHAZAM_TIME = time.monotonic()

                try:
                    url = API_URL % (str(uuid.uuid4()).upper(), str(uuid.uuid4()).upper())
                    r = requests.post(
                        url,
                        headers=HEADERS,
                        json=data,
                        timeout=10,
                    )
                    if r.status_code == 200:
                        try:
                            return r.json()
                        except Exception:
                            pass
                    elif r.status_code == 429:
                        logger.debug(f"Shazam rate limited (429), retrying attempt {attempt+1}/3...")
                    else:
                        logger.debug(f"Shazam returned HTTP {r.status_code}, retrying attempt {attempt+1}/3...")
                except Exception as e:
                    logger.debug(f"Shazam request failed: {e}, retrying attempt {attempt+1}/3...")

            time.sleep(0.8 * (attempt + 1))

        return {}

    Shazam.sendRecognizeRequest = _resilient_send_recognize_request


def normalize_artist(name: Optional[str]) -> str:
    """Normalize artist name for reliable equality comparison."""
    if not name:
        return ""
    s = clean_artist(name).lower()
    s = s.replace("’", "'").replace("`", "'").replace("“", '"').replace("”", '"')
    if s.startswith("the "):
        s = s[4:].strip()
    s = s.replace("&", "and")
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _artists_match(a1: Optional[str], a2: Optional[str]) -> bool:
    """
    Check if two artist names are equivalent.
    Strict comparison after normalization, preventing false collisions
    (e.g. Slash vs Slash featuring Myles Kennedy vs Slash's Snakepit).
    """
    if not a1 or not a2:
        return False
    n1 = normalize_artist(a1)
    n2 = normalize_artist(a2)
    if not n1 or not n2:
        return False
    return n1 == n2


def normalize_title(title: Optional[str]) -> str:
    """Normalize track title for strict equality comparison."""
    if not title:
        return ""
    t = clean_title(title).lower()
    t = re.sub(r"^\d+[\s.-]+", "", t)
    t = re.sub(r"\s*[\(\[\{][^\)\]\}]*[\)\]\}]", "", t)
    t = t.replace("’", "'").replace("`", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _matches_title(query_title: Optional[str], found_title: Optional[str]) -> bool:
    """
    Check if found_title genuinely matches query_title.
    Strict comparison: exact match (case-insensitive) or match after
    stripping brackets, live/remaster suffixes, and punctuation.
    Prevents single-word titles like 'Black' from matching 'Black, Black, Black'
    or 'Paint It Black' or 'Back In Black'.
    """
    if not query_title or not found_title:
        return False
    qt = clean_title(query_title).lower()
    ft = clean_title(found_title).lower()
    if qt == ft:
        return True

    # Strip bracketed content (e.g. "(Live)", "(Remastered 2004)")
    qt_clean = re.sub(r"\s*[\(\[\{][^\)\]\}]*[\)\]\}]", "", qt).strip(" ,.-_")
    ft_clean = re.sub(r"\s*[\(\[\{][^\)\]\}]*[\)\]\}]", "", ft).strip(" ,.-_")
    if qt_clean == ft_clean and qt_clean:
        return True

    nt1 = normalize_title(query_title)
    nt2 = normalize_title(found_title)
    if nt1 == nt2 and nt1:
        return True

    return False

def _cand_sort_key(item: tuple[float, SongInfo]) -> tuple:
    """
    Sort candidates by duration bucket, preferring original studio albums over compilations and earlier release years.
    Priority: same duration bucket -> lower compilation penalty -> earlier release year -> closer duration.
    """
    diff, cand = item
    diff_bucket = int(diff // 3.0)  # Diffs within 3 seconds are considered equal duration matches
    album_lower = (cand.album or "").lower()

    # Hard compilation markers
    _HARD_COMPILATION_WORDS = [
        "various", "compilation", "sampler", "greatest hits", "best of",
        "tribute", "karaoke", "ultimate", "essential", "collection",
    ]
    # Soft markers: genre-prefixed compilations like "Rock: The Train Kept a Rollin'" or "Live (Josh's Picks)"
    _SOFT_COMPILATION_PATTERNS = [
        r"^\w+:\s",                     # "Rock: ...", "Pop: ...", "Country: ..." etc.
        r"\blive\b",                    # "Live at ...", "MTV Live"
        r"\bsoundtrack\b",
        r"\bmotion picture\b",
        r"\boriginal score\b",
        r"josh'?s picks",
        r"let'?s play",
    ]

    compilation_penalty = 0
    if any(k in album_lower for k in _HARD_COMPILATION_WORDS):
        compilation_penalty = 5
    else:
        for pat in _SOFT_COMPILATION_PATTERNS:
            if re.search(pat, album_lower):
                compilation_penalty = 3
                break

    year_val = int(cand.year) if (cand.year and cand.year.isdigit()) else 9999
    return (diff_bucket, compilation_penalty, year_val, diff)


# ── Apple iTunes Search API ───────────────────────────────────────────────────

def lookup_by_itunes(
    artist: Optional[str],
    title: Optional[str],
    target_duration: Optional[float] = None,
) -> Optional[SongInfo]:
    """
    Lookup song metadata using the Apple iTunes Search API.
    Fast, reliable, free, and returns album name, artist, title, year, track number.
    When target_duration is provided, compares candidate durations to pick the exact
    track and resolve ambiguous titles belonging to different artists.
    """
    if not title:
        return None

    ca = clean_artist(artist) if artist else ""
    ct = clean_title(title) if title else ""

    queries = []
    if ca and ct:
        queries.append(f"{ca} {ct}")
    if ct:
        queries.append(ct)
    if artist and title and (artist != ca or title != ct):
        queries.append(f"{artist} {title}")

    url = "https://itunes.apple.com/search"
    candidates: list[tuple[float, SongInfo]] = []

    for q in queries:
        try:
            params = {
                "term": q,
                "entity": "song",
                "limit": 25 if target_duration else 5,
            }
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code != 200:
                continue

            data = resp.json()
            results = data.get("results", [])
            for item in results:
                found_title = item.get("trackName")
                found_artist = item.get("artistName")
                found_album = item.get("collectionName")
                track_num = item.get("trackNumber")
                release_date = item.get("releaseDate", "")
                year = release_date[:4] if len(release_date) >= 4 else None
                track_time_ms = item.get("trackTimeMillis")
                duration = float(track_time_ms) / 1000.0 if track_time_ms else None

                if found_title and found_artist and found_album:
                    # Standard match: found_artist matches ca, found_title matches ct
                    standard_artist = (not ca) or _artists_match(ca, found_artist)
                    standard_title = (not ct) or _matches_title(ct, found_title)
                    standard_match = standard_artist and standard_title

                    # Swapped match (filename was Title - Artist):
                    # found_artist matches ct AND found_title matches ca
                    swapped_artist = bool(ct and _artists_match(ct, found_artist))
                    swapped_title = bool(ca and _matches_title(ca, found_title))
                    swapped_match = swapped_artist and swapped_title

                    if not (standard_match or swapped_match):
                        continue

                    cand = SongInfo(
                        artist=found_artist,
                        album=found_album,
                        title=found_title,
                        track_number=track_num,
                        year=year,
                        duration=duration,
                        source="itunes",
                    )

                    if target_duration and duration:
                        diff = abs(duration - target_duration)
                        # When artist was not known, only accept candidates with close duration (<= 15s)
                        if not ca and diff > 15.0:
                            continue
                        if ca and diff > 60.0:
                            continue
                        candidates.append((diff, cand))
                    elif not target_duration:
                        logger.debug(f"[iTunes match] '{safe_display(found_artist)}' - '{safe_display(found_album)}' - '{safe_display(found_title)}'")
                        return cand

        except Exception as e:
            logger.debug(f"iTunes search failed for query '{q}': {e}")
            continue

        if target_duration and candidates:
            candidates.sort(key=_cand_sort_key)
            best_diff, best_cand = candidates[0]
            max_allowed = 60.0 if ca else 15.0
            if best_diff <= max_allowed:
                logger.debug(
                    f"[iTunes match with duration diff {best_diff:.1f}s] "
                    f"'{safe_display(best_cand.artist)}' - '{safe_display(best_cand.album)}' - '{safe_display(best_cand.title)}'"
                )
                return best_cand

    if target_duration and candidates:
        candidates.sort(key=_cand_sort_key)
        best_diff, best_cand = candidates[0]
        max_allowed = 60.0 if ca else 15.0
        if best_diff <= max_allowed:
            logger.debug(
                f"[iTunes match with duration diff {best_diff:.1f}s] "
                f"'{safe_display(best_cand.artist)}' - '{safe_display(best_cand.album)}' - '{safe_display(best_cand.title)}'"
            )
            return best_cand

    return None


# ── Shazam Audio Fingerprint Recognition ──────────────────────────────────────

def lookup_by_shazam(path: Path, target_duration: Optional[float] = None) -> Optional[SongInfo]:
    """
    Recognize song directly from audio content using Shazam.
    Identifies the exact artist and song title from audio fingerprint,
    resolving ambiguities when song titles belong to multiple artists.
    """
    if not HAS_SHAZAM:
        return None

    try:
        file_size = path.stat().st_size
        max_bytes = min(file_size, 4_000_000)
        with open(path, "rb") as fp:
            data = fp.read(max_bytes)

        shazam = Shazam(data)
        for i, (offset, result) in enumerate(shazam.recognizeSong()):
            if result and "track" in result:
                track = result["track"]
                found_artist = track.get("subtitle")
                found_title = track.get("title")

                # Extract album if available in track sections
                found_album = None
                for sec in track.get("sections", []):
                    if sec.get("type") == "SONG":
                        for meta in sec.get("metadata", []):
                            if meta.get("title", "").lower() == "album":
                                found_album = meta.get("text")
                                break

                if found_artist and found_title:
                    logger.debug(
                        f"[Shazam match] '{safe_display(found_artist)}' - '{safe_display(found_title)}'"
                    )
                    # Query iTunes with confirmed Shazam artist & title to get full official album & track info
                    itunes_match = lookup_by_itunes(found_artist, found_title, target_duration=target_duration)
                    if itunes_match:
                        itunes_match.source = "shazam"
                        return itunes_match

                    return SongInfo(
                        artist=found_artist,
                        album=found_album,
                        title=found_title,
                        duration=target_duration,
                        source="shazam",
                    )

            if i >= 4:
                break
    except Exception as exc:
        logger.debug(f"Shazam recognition failed for {safe_display(path.name)}: {exc}")

    return None


# ── MusicBrainz ────────────────────────────────────────────────────────────────

try:
    import musicbrainzngs as mb

    mb.set_useragent(
        "MusicOrganizer",
        "1.0",
        "https://github.com/FabioMassaretto/python_stream_downloader_converter",
    )
    HAS_MB = True
except ImportError:
    HAS_MB = False
    logger.warning("musicbrainzngs not installed; MusicBrainz lookup disabled.")

# ── AcoustID ───────────────────────────────────────────────────────────────────

try:
    import acoustid  # type: ignore

    HAS_ACOUSTID = True
except ImportError:
    HAS_ACOUSTID = False

_ACOUSTID_API_KEY = "cSpUJKpD"

# Rate-limit to MusicBrainz (max 1 req / sec)
_LAST_MB_CALL: float = 0.0
_MB_MIN_INTERVAL: float = 1.1


def _mb_throttle() -> None:
    global _LAST_MB_CALL
    gap = time.monotonic() - _LAST_MB_CALL
    if gap < _MB_MIN_INTERVAL:
        time.sleep(_MB_MIN_INTERVAL - gap)
    _LAST_MB_CALL = time.monotonic()


def _mb_recording_to_info(rec: dict) -> Optional[SongInfo]:
    """Convert a MusicBrainz recording dict into a SongInfo."""
    title = rec.get("title", "").strip()
    if not title:
        return None

    artist = ""
    credits = rec.get("artist-credit", [])
    for credit in credits:
        if isinstance(credit, dict) and "artist" in credit:
            artist = credit["artist"].get("name", "").strip()
            break

    album = ""
    releases = rec.get("release-list", [])
    if releases:
        # Prefer official releases
        official = [r for r in releases if (r.get("status") or "").lower() == "official"]
        best_release = official[0] if official else releases[0]
        album = best_release.get("title", "").strip()

    length_ms = rec.get("length")
    duration = float(length_ms) / 1000.0 if length_ms else None

    return SongInfo(
        artist=artist or None,
        album=album or None,
        title=title,
        duration=duration,
        source="musicbrainz",
    )


def lookup_by_text(artist: Optional[str], title: Optional[str]) -> Optional[SongInfo]:
    """Search MusicBrainz by artist + title (or title only)."""
    if not HAS_MB or not title:
        return None

    ca = clean_artist(artist) if artist else ""
    ct = clean_title(title) if title else ""

    queries = []
    # Query 1: exact clean
    q1_parts = []
    if ct:
        q1_parts.append(f'recording:"{ct}"')
    if ca:
        q1_parts.append(f'artist:"{ca}"')
    queries.append(" AND ".join(q1_parts))

    # Query 2: fallback without quotes for fuzzy match
    if ca and ct:
        queries.append(f"recording:{ct} AND artist:{ca}")

    for query in queries:
        _mb_throttle()
        try:
            result = mb.search_recordings(
                query=query,
                limit=5,
            )
            recordings = result.get("recording-list", [])
            for rec in recordings:
                rec_title = rec.get("title", "")
                if not _matches_title(ct, rec_title):
                    continue
                info = _mb_recording_to_info(rec)
                if info and info.is_organizable:
                    if ca:
                        rec_artist_lower = (info.artist or "").lower()
                        if ca.lower() not in rec_artist_lower and rec_artist_lower not in ca.lower():
                            continue
                    return info
        except Exception as exc:
            logger.debug(f"MusicBrainz search failed ({safe_display(query)!r}): {safe_display(str(exc))}")
            continue

    return None


def lookup_by_mbid(recording_id: str) -> Optional[SongInfo]:
    if not HAS_MB:
        return None

    _mb_throttle()
    try:
        result = mb.get_recording_by_id(
            recording_id,
            includes=["artists", "releases"],
        )
        rec = result.get("recording", {})
        return _mb_recording_to_info(rec)
    except Exception as exc:
        logger.debug(f"MusicBrainz MBID lookup failed ({recording_id}): {exc}")
        return None


def lookup_by_acoustid(path: Path) -> Optional[SongInfo]:
    """Fingerprint the file and look it up on AcoustID → MusicBrainz."""
    if not HAS_ACOUSTID:
        return None

    try:
        duration, fp = acoustid.fingerprint_file(str(path))
    except Exception as exc:
        logger.debug(f"AcoustID fingerprint failed for {path.name}: {exc}")
        return None

    try:
        results = list(
            acoustid.lookup(
                _ACOUSTID_API_KEY,
                fp,
                duration,
                meta="recordings releasegroups",
            )
        )
    except Exception as exc:
        logger.debug(f"AcoustID lookup failed for {path.name}: {exc}")
        return None

    for score, recording_id, title, artist in results:
        if score < 0.5:
            continue
        if recording_id:
            info = lookup_by_mbid(recording_id)
            if info and info.is_organizable and info.album:
                return info
        if title and artist:
            return SongInfo(artist=artist, title=title, source="acoustid")

    return None


def lookup_online(
    artist: Optional[str],
    title: Optional[str],
    target_duration: Optional[float] = None,
) -> Optional[SongInfo]:
    """
    Search online across all available providers (iTunes, MusicBrainz)
    to find the song and its album.
    When target_duration is provided, compares candidate durations to disambiguate songs.
    """
    # 1. Try iTunes first (fastest, most complete album metadata)
    itunes_info = lookup_by_itunes(artist, title, target_duration=target_duration)
    if itunes_info and itunes_info.album:
        return itunes_info

    # If artist & title were provided, try swapped in case filename had Title - Artist
    if artist and title:
        swapped_itunes = lookup_by_itunes(title, artist, target_duration=target_duration)
        if swapped_itunes and swapped_itunes.album:
            return swapped_itunes

    # 2. Try MusicBrainz
    mb_info = lookup_by_text(artist, title)
    if mb_info and mb_info.album:
        return mb_info

    if artist and title:
        swapped_mb = lookup_by_text(title, artist)
        if swapped_mb and swapped_mb.album:
            return swapped_mb

    # 3. If iTunes found artist+title but no album, return it
    if itunes_info:
        return itunes_info

    return mb_info
