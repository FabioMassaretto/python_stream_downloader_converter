"""
Parse artist / title hints from common filename patterns:

  Artist - Title.mp3
  Artist - Album - Title.mp3
  01 - Title.mp3
  01 - Artist - Title.mp3
  Artist_Title.mp3
  Artist "Title".mp3
  Artist: Title.mp3
  Title | Artist.mp3
  Title // Artist.mp3
  Title.mp3
"""
import re
from pathlib import Path
from typing import Optional

from tools.music_organizer.organizer.models import SongInfo


def normalize_string(s: str) -> str:
    """Normalize unicode characters commonly found in video titles and tags."""
    # Replace unicode dashes with standard dash
    s = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]", "-", s)
    # Replace unicode quotes with standard quotes
    s = re.sub(r"[\u201c\u201d\u201e\u201f\uff02]", '"', s)
    s = re.sub(r"[\u2018\u2019\u201a\u201b\uff07]", "'", s)
    # Replace unicode slashes and solidus
    s = re.sub(r"[\u29f8\uff0f]", "/", s)
    # Replace unicode colons
    s = re.sub(r"[\uff1a]", ":", s)
    # Replace unicode pipes
    s = re.sub(r"[\uff5c]", "|", s)
    # Replace non-breaking spaces
    s = re.sub(r"[\u00a0\u200b\ufeff]", " ", s)
    # Normalize AC?DC or AC_DC to AC/DC
    s = re.sub(r"(?i)\bAC[\?_]DC\b", "AC/DC", s)
    return s.strip()


_BRACKET_JUNK = re.compile(
    r"(?i)\s*[\(\[\{][^\)\]\}]*(?:"
    r"official|video|audio|lyrics?|visualizer|clip|film|mv|"
    r"4k|hd|hq|1080p|720p|60fps|dvd|"
    r"remaster|remix|mix|unplugged|tour|concert|stadium|festival|acoustic|session|"
    r"version|explicit|clean|extended|soundtrack|ost|"
    r"legendado|traduc|sub\s+esp|thai\s+sub|color\s+coded"
    r")[^\)\]\}]*[\)\]\}]"
)

_LIVE_BRACKET = re.compile(
    r"(?i)\s*[\(\[\{][^\)\]\}]*\blive\b[^\)\]\}]*[\)\]\}]"
)

_TRAILING_JUNK = re.compile(
    r"(?i)\s*(?:"
    r"(?:official\s+)?(?:music\s+|hd\s+|4k\s+)?(?:video|audio|lyric\s+video|lyrics?|visualizer|mv)|"
    r"\blive\s+(?:at|from|in)\b.*|\blive\s*$|"
    r"remastered(?:\s+\d{4})?|remix(?:ed)?|"
    r"guitar\s+center\s+sessions.*|from\s+the\s+basement.*|"
    r"1080p\s+60fps\s+dvd.*"
    r")\s*$"
)


def clean_artist(artist: Optional[str]) -> Optional[str]:
    """Clean common artifacts from artist names."""
    if not artist:
        return None
    cleaned = normalize_string(artist)
    cleaned = re.sub(r"(?i)\s*[-–]\s*topic$", "", cleaned)
    cleaned = re.sub(r"^\s*\[\s*\d+\s*\]\s*", "", cleaned)
    cleaned = re.sub(r"(?i)\s*official$", "", cleaned)
    cleaned = re.sub(r"(?i)\s*vevo$", "", cleaned)
    cleaned = cleaned.strip(" '\"-_")
    return cleaned or None


def clean_title(title: Optional[str]) -> Optional[str]:
    """Strip YouTube video suffixes, quality tags, and junk from titles."""
    if not title:
        return None
    cleaned = normalize_string(title)

    # Strip pipe sections like | From The Basement
    cleaned = re.sub(r"\s*\|.*$", "", cleaned)

    # Repeatedly strip bracket junk
    for _ in range(3):
        cleaned = _BRACKET_JUNK.sub("", cleaned)
        cleaned = _LIVE_BRACKET.sub("", cleaned)

    # Strip trailing junk
    cleaned = _TRAILING_JUNK.sub("", cleaned)

    # Strip wrapping quotes and whitespace
    cleaned = cleaned.strip(" '\"-_")
    return cleaned or None


def _clean(s: str) -> str:
    return normalize_string(s).strip(" ._-\"'")


def parse_filename(path: Path) -> Optional[SongInfo]:
    """
    Extract title and artist hints from a filename.
    Returns None only if the stem is empty.
    """
    raw_stem = path.stem.strip()
    if not raw_stem:
        return None

    stem = normalize_string(raw_stem)
    # Strip leading track bracket prefixes like [05]
    stem = re.sub(r"^\s*\[\s*\d+\s*\]\s*", "", stem)

    # 1. "Title" de/by Artist  (e.g. "Impatient" de Sascha Ende)
    m = re.match(r'^(?:")?(.+?)(?:")?\s+(?:de|by)\s+(.+)$', stem, re.IGNORECASE)
    if m:
        t, a = m.group(1), m.group(2)
        ct, ca = clean_title(t), clean_artist(a)
        if ct:
            return SongInfo(artist=ca, title=ct, source="filename")

    # 2. Artist Performs "Title" Live ...
    m = re.match(r'^(.+?)\s+Performs\s+["\'](.+?)["\']', stem, re.IGNORECASE)
    if m:
        a, t = m.group(1), m.group(2)
        ct, ca = clean_title(t), clean_artist(a)
        if ct:
            return SongInfo(artist=ca, title=ct, source="filename")

    # 3. Artist "Title" ... e.g. Nickelback "Bottoms Up" Lyric Video
    m = re.match(r'^([^\"]+?)\s+["\']([^"\']+)["\']', stem)
    if m:
        a, t = m.group(1), m.group(2)
        ct, ca = clean_title(t), clean_artist(a)
        if ct:
            return SongInfo(artist=ca, title=ct, source="filename")

    # 4. "01 - Artist - Title"
    m = re.match(r"^(?P<track>\d{1,3})\s*-\s*(?P<artist>.+?)\s*-\s*(?P<title>.+)$", stem)
    if m:
        gd = m.groupdict()
        track = int(gd["track"])
        ca = clean_artist(gd["artist"])
        ct = clean_title(gd["title"]) or _clean(gd["title"])
        if ct:
            return SongInfo(artist=ca, title=ct, track_number=track, source="filename")

    # 5. "01 - Title"
    m = re.match(r"^(?P<track>\d{1,3})\s*-\s*(?P<title>.+)$", stem)
    if m:
        gd = m.groupdict()
        track = int(gd["track"])
        ct = clean_title(gd["title"]) or _clean(gd["title"])
        if ct:
            return SongInfo(title=ct, track_number=track, source="filename")

    # 6. Pipe separated: Title | Artist | Extra (e.g. Mexicola | Queens Of The Stone Age | ...)
    if "|" in stem:
        parts = [p.strip() for p in stem.split("|") if p.strip()]
        if len(parts) >= 2:
            ct = clean_title(parts[0])
            ca = clean_artist(parts[1])
            if ct:
                return SongInfo(artist=ca, title=ct, source="filename")

    # 7. Double slash: white dress // lana del rey
    if "//" in stem:
        parts = [p.strip() for p in stem.split("//") if p.strip()]
        if len(parts) >= 2:
            ct = clean_title(parts[0])
            ca = clean_artist(parts[1])
            if ct:
                return SongInfo(artist=ca, title=ct, source="filename")

    # 8. Colon separated: Artist: Title (e.g. Paramore: Decode)
    if ":" in stem:
        parts = [p.strip() for p in stem.split(":", 1) if p.strip()]
        if len(parts) == 2:
            part0 = parts[0]
            part1 = parts[1]
            # Try part0 as artist, part1 as title
            ca = clean_artist(part0)
            ct = clean_title(part1) or _clean(part1)
            if ct:
                return SongInfo(artist=ca, title=ct, source="filename")

    # 9. Standard "Artist - Title"
    if " - " in stem:
        parts = stem.split(" - ", 1)
        ca = clean_artist(parts[0])
        ct = clean_title(parts[1]) or _clean(parts[1])
        if ct:
            return SongInfo(artist=ca, title=ct, source="filename")

    # 10. Artist_Title (single underscore)
    if stem.count("_") == 1:
        parts = stem.split("_", 1)
        ca = clean_artist(parts[0])
        ct = clean_title(parts[1]) or _clean(parts[1])
        if ct and ca:
            return SongInfo(artist=ca, title=ct, source="filename")

    # Fallback: whole cleaned stem as Title
    fallback_title = clean_title(stem) or _clean(stem)
    return SongInfo(title=fallback_title, source="filename")
