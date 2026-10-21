"""
Online metadata lookup via:
  1. AcoustID  (audio fingerprint → MusicBrainz recording ID)  – needs fpcalc
  2. MusicBrainz text search  (artist + title / title only)
"""
import time
import logging
from pathlib import Path
from typing import Optional

from organizer.models import SongInfo

logger = logging.getLogger(__name__)

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

_ACOUSTID_API_KEY = "cSpUJKpD"  # public test key – replace with your own

# Polite rate-limit to MusicBrainz (max 1 req / sec without auth)
_LAST_MB_CALL: float = 0.0
_MB_MIN_INTERVAL: float = 1.1  # seconds


def _mb_throttle() -> None:
    global _LAST_MB_CALL
    gap = time.monotonic() - _LAST_MB_CALL
    if gap < _MB_MIN_INTERVAL:
        time.sleep(_MB_MIN_INTERVAL - gap)
    _LAST_MB_CALL = time.monotonic()


# ── AcoustID lookup ────────────────────────────────────────────────────────────

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
        if title and artist:
            return SongInfo(artist=artist, title=title, source="acoustid")

    return None


# ── MusicBrainz text search ───────────────────────────────────────────────────

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
        album = releases[0].get("title", "").strip()

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

    query_parts = []
    if title:
        query_parts.append(f'recording:"{title}"')
    if artist:
        query_parts.append(f'artist:"{artist}"')
    query = " AND ".join(query_parts)

    _mb_throttle()
    try:
        result = mb.search_recordings(
            query=query,
            limit=5,
            includes=["artist-credits", "releases"],
        )
    except Exception as exc:
        logger.debug(f"MusicBrainz search failed ({query!r}): {exc}")
        return None

    recordings = result.get("recording-list", [])
    for rec in recordings:
        info = _mb_recording_to_info(rec)
        if info and info.is_organizable:
            return info

    return None


# ── MusicBrainz lookup by recording ID ────────────────────────────────────────

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
