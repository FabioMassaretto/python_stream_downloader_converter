"""
Online metadata lookup via:
  1. Apple iTunes Search API (fast, comprehensive album metadata, no rate-limit)
  2. MusicBrainz text search (artist + title / title only)
  3. AcoustID (audio fingerprint → MusicBrainz recording ID, optional)
"""
import time
import logging
import requests
from pathlib import Path
from typing import Optional

from tools.music_organizer.organizer.models import SongInfo
from tools.music_organizer.organizer.filename_parser import clean_artist, clean_title
from tools.music_organizer.organizer.utils import safe_display

logger = logging.getLogger(__name__)

# ── Apple iTunes Search API ───────────────────────────────────────────────────

def lookup_by_itunes(artist: Optional[str], title: Optional[str]) -> Optional[SongInfo]:
    """
    Lookup song metadata using the Apple iTunes Search API.
    Fast, reliable, free, and returns album name, artist, title, year, track number.
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

    for q in queries:
        try:
            params = {
                "term": q,
                "entity": "song",
                "limit": 5,
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

                if found_title and found_artist and found_album:
                    # If we had an artist query, verify it matches
                    if ca:
                        ca_lower = ca.lower()
                        fa_lower = found_artist.lower()
                        ct_lower = ct.lower() if ct else ""
                        artist_matches = (ca_lower in fa_lower or fa_lower in ca_lower)
                        if not artist_matches and ct_lower and (ct_lower in fa_lower or fa_lower in ct_lower):
                            artist_matches = True
                        if not artist_matches:
                            continue

                    logger.debug(f"[iTunes match] '{safe_display(found_artist)}' - '{safe_display(found_album)}' - '{safe_display(found_title)}'")
                    return SongInfo(
                        artist=found_artist,
                        album=found_album,
                        title=found_title,
                        track_number=track_num,
                        year=year,
                        source="itunes",
                    )
        except Exception as e:
            logger.debug(f"iTunes search failed for query '{q}': {e}")
            continue

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

    return SongInfo(
        artist=artist or None,
        album=album or None,
        title=title,
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
                info = _mb_recording_to_info(rec)
                if info and info.is_organizable:
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


def lookup_online(artist: Optional[str], title: Optional[str]) -> Optional[SongInfo]:
    """
    Search online across all available providers (iTunes, MusicBrainz)
    to find the song and its album.
    """
    # 1. Try iTunes first (fastest, most complete album metadata)
    itunes_info = lookup_by_itunes(artist, title)
    if itunes_info and itunes_info.album:
        return itunes_info

    # If artist & title were provided, try swapped in case filename had Title - Artist
    if artist and title:
        swapped_itunes = lookup_by_itunes(title, artist)
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
