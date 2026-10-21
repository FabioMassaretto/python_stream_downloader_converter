"""Read embedded tags from audio files using mutagen."""
from pathlib import Path
from typing import Optional

from organizer.models import SongInfo

try:
    import mutagen
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3NoHeaderError
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False


def _first(mapping, *keys) -> Optional[str]:
    """Return the first non-empty string value found in *mapping* for *keys*."""
    for key in keys:
        val = mapping.get(key)
        if val:
            if isinstance(val, (list, tuple)):
                val = val[0]
            text = str(val).strip()
            if text:
                return text
    return None


def _track_num(raw: Optional[str]) -> Optional[int]:
    if not raw:
        return None
    # e.g. "3/12" → 3
    try:
        return int(str(raw).split("/")[0])
    except (ValueError, IndexError):
        return None


def read_tags(path: Path) -> Optional[SongInfo]:
    """
    Return a SongInfo populated from the file's embedded tags,
    or None if the file cannot be opened or has no useful tags.
    """
    if not HAS_MUTAGEN:
        return None

    try:
        audio = MutagenFile(path, easy=True)
    except Exception:
        return None

    if audio is None:
        return None

    tags = audio.tags or {}

    artist = _first(tags, "artist", "albumartist", "performer")
    album  = _first(tags, "album")
    title  = _first(tags, "title")
    year   = _first(tags, "date", "year", "originaldate")
    track  = _track_num(_first(tags, "tracknumber"))

    # Year: keep only the 4-digit part
    if year and len(year) > 4:
        year = year[:4]

    if not (artist or album or title):
        return None

    return SongInfo(
        artist=artist,
        album=album,
        title=title,
        track_number=track,
        year=year,
        source="tags",
    )
