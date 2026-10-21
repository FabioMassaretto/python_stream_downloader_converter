"""
Core pipeline: given a Path, produce the best available SongInfo,
then copy/move the file to its organized destination.
"""
import logging
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional

from organizer.models import SongInfo
from organizer.tag_reader import read_tags
from organizer.filename_parser import parse_filename
from organizer import online_lookup

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
    Try, in order:
      1. Embedded tags (mutagen)
      2. AcoustID fingerprint  (if fpcalc available)
      3. MusicBrainz text search  (if tags / filename gave us a hint)
      4. Filename parsing
    Returns None only if absolutely nothing useful was found.
    """
    # Step 1 – embedded tags
    info = read_tags(path)
    if info and info.is_organizable and info.album:
        logger.debug(f"[tags-complete] {path.name}")
        return info

    # Step 2 – AcoustID (audio fingerprint) – only if file is big enough (>1 MB)
    if use_online and path.stat().st_size > 1_000_000:
        acoustid_info = online_lookup.lookup_by_acoustid(path)
        if acoustid_info:
            info = _merge(info, acoustid_info)
            if info and info.is_organizable and info.album:
                logger.debug(f"[acoustid-complete] {path.name}")
                return info

    # Step 3 – MusicBrainz text search using whatever we know so far
    if use_online:
        # Build hint: prefer tags, then fall back to filename
        hint = info or parse_filename(path)
        if hint and (hint.artist or hint.title):
            mb_info = online_lookup.lookup_by_text(hint.artist, hint.title)
            if mb_info:
                info = _merge(info, mb_info)
                if info and info.is_organizable:
                    logger.debug(f"[musicbrainz] {path.name}")
                    return info

    # Step 4 – filename parsing as last resort
    fn_info = parse_filename(path)
    if fn_info:
        info = _merge(info, fn_info)

    if info and info.is_organizable:
        logger.debug(f"[filename] {path.name}")
        return info

    logger.debug(f"[unresolvable] {path.name}")
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

    return dest
