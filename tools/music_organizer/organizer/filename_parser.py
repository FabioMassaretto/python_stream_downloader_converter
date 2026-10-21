"""
Parse artist / title hints from common filename patterns:

  Artist - Title.mp3
  Artist - Album - Title.mp3
  01 - Title.mp3
  01 - Artist - Title.mp3
  Artist_Title.mp3
  Title.mp3
"""
import re
from pathlib import Path
from typing import Optional

from organizer.models import SongInfo

# Patterns tried in order (most specific first)
_PATTERNS: list[tuple[str, re.Pattern]] = [
    # "01 - Artist - Title"
    (
        "track-artist-title",
        re.compile(
            r"^(?P<track>\d{1,3})\s*[-–]\s*(?P<artist>.+?)\s*[-–]\s*(?P<title>.+)$"
        ),
    ),
    # "01 - Title"   (must come before artist-title so pure numbers stay as track)
    (
        "track-title",
        re.compile(r"^(?P<track>\d{1,3})\s*[-–]\s*(?P<title>.+)$"),
    ),
    # "Artist - Title"  (reject when left-side is purely numeric – already handled above)
    (
        "artist-title",
        re.compile(r"^(?P<artist>(?!\d+\s*$).+?)\s*[-–]\s*(?P<title>.+)$"),
    ),
    # "Artist_Title"  (underscore separator, only when it contains exactly one)
    (
        "artist_title",
        re.compile(r"^(?P<artist>[^_]+)_(?P<title>[^_]+)$"),
    ),
]


def _clean(s: str) -> str:
    return s.strip(" ._-")


def parse_filename(path: Path) -> Optional[SongInfo]:
    """
    Try to extract at least a title (and ideally artist) from the filename.
    Returns None only if the stem is empty.
    """
    stem = path.stem.strip()
    if not stem:
        return None

    for name, pattern in _PATTERNS:
        m = pattern.match(stem)
        if not m:
            continue
        gd = m.groupdict()
        artist = _clean(gd["artist"]) if "artist" in gd else None
        title  = _clean(gd["title"])
        track  = int(gd["track"]) if "track" in gd else None

        if title:
            return SongInfo(
                artist=artist or None,
                title=title,
                track_number=track,
                source="filename",
            )

    # Absolute fallback: whole stem becomes the title
    return SongInfo(title=_clean(stem), source="filename")
