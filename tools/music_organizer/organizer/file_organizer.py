"""
Core pipeline: given a Path, produce the best available SongInfo,
then copy/move the file to its organized destination.
"""
import logging
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional

from tools.music_organizer.organizer.models import SongInfo
from tools.music_organizer.organizer.tag_reader import read_tags, write_tags
from tools.music_organizer.organizer.filename_parser import parse_filename
from tools.music_organizer.organizer.utils import safe_display
from tools.music_organizer.organizer import online_lookup

logger = logging.getLogger(__name__)


class FileMode(str, Enum):
    COPY = "copy"
    MOVE = "move"


# ── Metadata resolution pipeline ──────────────────────────────────────────────

def _merge(base: Optional[SongInfo], extra: Optional[SongInfo]) -> Optional[SongInfo]:
    """Fill missing fields in *base* from *extra*, keeping base's source label."""
    if not base:
        return extra
    if not extra:
        return base

    if not base.artist and extra.artist:
        base.artist = extra.artist
    if not base.album and extra.album:
        base.album = extra.album
    if not base.title and extra.title:
        base.title = extra.title
    if not base.track_number and extra.track_number:
        base.track_number = extra.track_number
    if not base.year and extra.year:
        base.year = extra.year

    return base


def resolve_metadata(
    path: Path,
    use_online: bool = True,
) -> Optional[SongInfo]:
    """
    Resolve song metadata using embedded tags, online lookup (iTunes & MusicBrainz),
    and filename parsing.

    Resolution order:
      1. Embedded tags (mutagen) - if artist, title, AND album are present, return immediately.
      2. Combine with filename parsing hints.
      3. If album or artist is missing and use_online is True:
         a. AcoustID audio fingerprinting (if available and file > 1MB).
         b. Online search (iTunes Search API first, MusicBrainz fallback).
            If found, official artist, album, title, year, and track number are used.
      4. If online search fails or is disabled:
         - If artist and title are known, keep album=None (placed in "Unknown Album").
         - If artist or title cannot be identified, return None (file left as-is).
    """
    # Step 1 – embedded tags
    info = read_tags(path)
    if info and info.is_organizable and info.album:
        logger.debug(f"[tags-complete] {safe_display(path.name)}")
        return info

    # Step 2 – filename hint
    fn_info = parse_filename(path)
    if not info:
        info = fn_info
    elif fn_info:
        info = _merge(info, fn_info)

    # Step 3 – AcoustID (audio fingerprint) – only if file is big enough (>1 MB)
    if use_online and path.stat().st_size > 1_000_000:
        acoustid_info = online_lookup.lookup_by_acoustid(path)
        if acoustid_info:
            info = _merge(info, acoustid_info)
            if info and info.is_organizable and info.album:
                logger.debug(f"[acoustid-complete] {safe_display(path.name)}")
                return info

    # Step 4 – Online lookup via iTunes & MusicBrainz
    if use_online and info and (info.artist or info.title):
        online_info = online_lookup.lookup_online(info.artist, info.title)
        if online_info:
            # Prefer clean official metadata from online lookup
            if online_info.album:
                info.album = online_info.album
            if online_info.artist:
                info.artist = online_info.artist
            if online_info.title:
                info.title = online_info.title
            if online_info.year and not info.year:
                info.year = online_info.year
            if online_info.track_number and not info.track_number:
                info.track_number = online_info.track_number
            info.source = online_info.source
            logger.debug(f"[{online_info.source}-complete] {safe_display(path.name)} -> {info}")
            return info

    # Step 5 – Fallback check
    # If we have both artist and title, but no album could be found anywhere:
    # return info with album=None (will be routed to "Unknown Album")
    if info and info.is_organizable:
        logger.debug(f"[fallback-artist-title] {safe_display(path.name)} -> {info}")
        return info

    # If neither artist nor title could be found (not a song or unidentifiable):
    # return None so the file is left untouched as-is.
    logger.debug(f"[unresolvable] {safe_display(path.name)}")
    return None


# ── File operation ─────────────────────────────────────────────────────────────

def organize_file(
    src: Path,
    info: SongInfo,
    output_root: Path,
    mode: FileMode = FileMode.COPY,
    dry_run: bool = False,
) -> Optional[Path]:
    """
    Copy or move *src* to its organised destination.
    Also embeds resolved metadata tags into the destination file.
    Returns the destination path, or None on failure.
    """
    dest = info.dest_path(output_root, src.suffix.lower())

    if dest == src:
        logger.info(f"[skip] Already in place: {src.name}")
        return dest

    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Handle duplicate filenames
        counter = 1
        original_stem = dest.stem
        while dest.exists() and dest.resolve() != src.resolve():
            dest = dest.with_stem(f"{original_stem} ({counter})")
            counter += 1

        try:
            if mode == FileMode.MOVE:
                shutil.move(str(src), str(dest))
            else:
                shutil.copy2(str(src), str(dest))
        except Exception as exc:
            logger.error(f"Failed to {mode.value} {src.name} → {dest}: {exc}")
            return None

        # Embed resolved tags into destination file
        try:
            write_tags(dest, info)
        except Exception as exc:
            logger.debug(f"Could not embed ID3 tags into {dest.name}: {exc}")

    return dest
