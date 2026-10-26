"""
Core pipeline: given a Path, produce the best available SongInfo,
then copy/move the file to its organized destination.
"""
import logging
import shutil
from enum import Enum
from pathlib import Path
from typing import Optional
try:
    from organizer.models import SongInfo
    from organizer.tag_reader import read_tags, write_tags, get_audio_duration
    from organizer.filename_parser import parse_filename, is_lesson_or_tutorial, clean_title
    from organizer.utils import safe_display
    from organizer import online_lookup
except ImportError:
    from tools.music_organizer.organizer.models import SongInfo
    from tools.music_organizer.organizer.tag_reader import read_tags, write_tags, get_audio_duration
    from tools.music_organizer.organizer.filename_parser import parse_filename, is_lesson_or_tutorial, clean_title
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
    if not base.duration and extra.duration:
        base.duration = extra.duration

    return base


def _duration_matches(dur1: Optional[float], dur2: Optional[float], tolerance: float = 25.0) -> bool:
    """Return True if both durations are close within tolerance, or if either is unknown."""
    if dur1 is None or dur2 is None:
        return True
    return abs(dur1 - dur2) <= tolerance


def _two_sources_agree(s1: Optional[SongInfo], s2: Optional[SongInfo]) -> bool:
    """Return True if both sources agree on artist and title."""
    if not s1 or not s2:
        return False
    if not s1.artist or not s2.artist or not s1.title or not s2.title:
        return False
    return online_lookup._artists_match(s1.artist, s2.artist) and online_lookup._matches_title(s1.title, s2.title)


def resolve_metadata(
    path: Path,
    use_online: bool = True,
) -> Optional[SongInfo]:
    """
    Resolve song metadata using strict multi-source consensus:
      1. Lesson/tutorial detection – guitar lessons, tutorials, and classes
         are not commercial songs and are routed to Unrecognized.
      2. Embedded tags & filename parsing to extract local hints.
         Embedded tags are validated against duration; mismatching tags are rejected.
      3. Phase 1 – Metadata comparison (iTunes vs MusicBrainz vs Filename):
         Requires at least 2 sources to agree on artist and title with matching duration.
      4. Phase 2 – Shazam audio fingerprinting (ground-truth tiebreaker):
         Invoked when text lookups return conflicting/opposite artists, title is ambiguous,
         or 2 sources have not confirmed the song.
         If Shazam finds an audio match, it is verified against a 2nd source (iTunes/MusicBrainz/Filename).
      5. Title guard – if lookups return a completely different title from the file's title
         without an authoritative audio fingerprint conclusion, the file is routed to Unrecognized.
      6. If 100% certainty is not reached, returns None (file is moved to Unrecognized keeping original filename).
    """
    duration = get_audio_duration(path)

    # 1. Lesson/tutorial detection in filename or directory path
    if is_lesson_or_tutorial(path.name) or is_lesson_or_tutorial(str(path)):
        logger.info(f"[lesson/tutorial detected] {safe_display(path.name)} -> routing to Unrecognized")
        return None

    # 2. Local cues: embedded tags
    tag_info = read_tags(path)
    if tag_info:
        if (tag_info.title and is_lesson_or_tutorial(tag_info.title)) or (tag_info.album and is_lesson_or_tutorial(tag_info.album)):
            logger.info(f"[lesson/tutorial in tags] {safe_display(path.name)} -> routing to Unrecognized")
            return None

        # Sanity check: if online mode is enabled, verify embedded tags against official release duration
        # to ensure old corrupted tags (e.g. HeDLesS on guitar lesson or Ronan Browne on Pearl Jam) are discarded
        if use_online and tag_info.artist and tag_info.title and duration:
            online_check = online_lookup.lookup_by_itunes(tag_info.artist, tag_info.title, target_duration=duration)
            if online_check and online_check.duration:
                if abs(duration - online_check.duration) > 45.0:
                    logger.info(
                        f"[tag-duration-mismatch] {safe_display(path.name)}: "
                        f"file is {duration:.1f}s but tags '{tag_info.artist} - {tag_info.title}' is {online_check.duration:.1f}s -> discarding invalid tags"
                    )
                    tag_info = None

    # 3. Local cues: filename and folder hints
    fn_info = parse_filename(path)
    if not fn_info or not fn_info.artist:
        generic_dirs = {
            "organized", "audio", "converted", "downloaded", "video",
            "media", "library", "unrecognized", "unknown album", "unknown artist",
            "music", "songs", "tmp", "temp"
        }
        parent_name = path.parent.name.strip()
        grandparent_name = path.parent.parent.name.strip() if len(path.parents) >= 2 else ""

        folder_artist = None
        # Check standard Artist / Album / Track structure:
        if grandparent_name and grandparent_name.lower() not in generic_dirs and parent_name.lower() not in generic_dirs:
            try:
                from organizer.filename_parser import clean_artist
            except ImportError:
                from tools.music_organizer.organizer.filename_parser import clean_artist
            folder_artist = clean_artist(grandparent_name)
        elif parent_name.lower() not in generic_dirs:
            try:
                from organizer.filename_parser import clean_artist
            except ImportError:
                from tools.music_organizer.organizer.filename_parser import clean_artist
            folder_artist = clean_artist(parent_name)

        if folder_artist:
            if fn_info:
                fn_info.artist = folder_artist
            else:
                fn_info = SongInfo(artist=folder_artist, title=path.stem, source="filename")

    # If offline mode (use_online=False):
    if not use_online:
        if tag_info and tag_info.is_organizable and tag_info.album:
            return tag_info
        if fn_info and fn_info.is_organizable:
            return _merge(tag_info, fn_info)
        return None

    # 3. Online Consensus Resolution:
    # First line of truth: Shazam audio fingerprinting (listens to the actual audio waveform)
    shazam_info = online_lookup.lookup_by_shazam(path, target_duration=duration)

    if shazam_info and shazam_info.artist and shazam_info.title:
        # Cross-verify Shazam's identification with a 2nd online service or filename:
        # Check iTunes
        itunes_shz = online_lookup.lookup_by_itunes(shazam_info.artist, shazam_info.title, target_duration=duration)
        if itunes_shz and _two_sources_agree(shazam_info, itunes_shz) and _duration_matches(duration, itunes_shz.duration, 60.0):
            confirmed = _merge(shazam_info, itunes_shz)
            logger.debug(f"[confirmed: shazam + itunes] {safe_display(path.name)} -> {confirmed}")
            return confirmed

        # Check MusicBrainz
        mb_shz = online_lookup.lookup_by_text(shazam_info.artist, shazam_info.title)
        if mb_shz and _two_sources_agree(shazam_info, mb_shz) and _duration_matches(duration, mb_shz.duration, 60.0):
            confirmed = _merge(shazam_info, mb_shz)
            logger.debug(f"[confirmed: shazam + musicbrainz] {safe_display(path.name)} -> {confirmed}")
            return confirmed

        # Check Filename
        if fn_info and fn_info.artist and _two_sources_agree(fn_info, shazam_info):
            confirmed = _merge(shazam_info, itunes_shz) if itunes_shz else shazam_info
            logger.debug(f"[confirmed: filename + shazam] {safe_display(path.name)} -> {confirmed}")
            return confirmed

    # When audio fingerprinting did NOT identify the track:
    # Check if audio exceeds standard song duration (>12 min / 720s)
    if duration and duration > 720.0:
        logger.info(
            f"[unrecognized-long-audio] {safe_display(path.name)}: "
            f"duration {duration:.1f}s exceeds song threshold and was not recognized -> routing to Unrecognized"
        )
        return None

    # Secondary resolution: Metadata comparison (iTunes vs MusicBrainz vs Filename)
    local_title = (fn_info.title if fn_info and fn_info.title else None) or clean_title(path.stem)
    local_artist = fn_info.artist if fn_info and fn_info.artist else None

    # If filename didn't have artist, check parent folder
    if not local_artist:
        generic_dirs = {
            "organized", "audio", "converted", "downloaded", "video",
            "media", "library", "unrecognized", "unknown album", "unknown artist",
            "music", "songs", "tmp", "temp"
        }
        parent_name = path.parent.name.strip()
        grandparent_name = path.parent.parent.name.strip() if len(path.parents) >= 2 else ""

        if grandparent_name and grandparent_name.lower() not in generic_dirs and parent_name.lower() not in generic_dirs:
            try:
                from organizer.filename_parser import clean_artist
            except ImportError:
                from tools.music_organizer.organizer.filename_parser import clean_artist
            local_artist = clean_artist(grandparent_name)
        elif parent_name.lower() not in generic_dirs:
            try:
                from organizer.filename_parser import clean_artist
            except ImportError:
                from tools.music_organizer.organizer.filename_parser import clean_artist
            local_artist = clean_artist(parent_name)

    itunes_info = None
    mb_info = None
    if local_title:
        itunes_info = online_lookup.lookup_by_itunes(local_artist, local_title, target_duration=duration)
        mb_info = online_lookup.lookup_by_text(local_artist, local_title)

    # Check for opposite / conflicting results between online text providers
    opposite_results = False
    if itunes_info and mb_info and itunes_info.artist and mb_info.artist:
        if not online_lookup._artists_match(itunes_info.artist, mb_info.artist):
            opposite_results = True
            logger.info(
                f"[opposite-results] {safe_display(path.name)}: iTunes returned '{itunes_info.artist}' "
                f"but MusicBrainz returned '{mb_info.artist}' -> routing to Unrecognized"
            )
            return None

    # Require 2 sources to agree:
    # 1. iTunes + MusicBrainz agree
    if itunes_info and mb_info and _two_sources_agree(itunes_info, mb_info):
        if _duration_matches(duration, itunes_info.duration, 25.0):
            if not local_title or online_lookup._matches_title(local_title, itunes_info.title):
                logger.debug(f"[confirmed: itunes + musicbrainz] {safe_display(path.name)}")
                return _merge(itunes_info, mb_info)

    # 2. Filename + iTunes agree
    if fn_info and fn_info.artist and itunes_info and _two_sources_agree(fn_info, itunes_info):
        if _duration_matches(duration, itunes_info.duration, 25.0):
            if not mb_info or online_lookup._artists_match(fn_info.artist, mb_info.artist):
                logger.debug(f"[confirmed: filename + itunes] {safe_display(path.name)}")
                return itunes_info

    # 3. Filename + MusicBrainz agree
    if fn_info and fn_info.artist and mb_info and _two_sources_agree(fn_info, mb_info):
        if _duration_matches(duration, mb_info.duration, 25.0):
            if not itunes_info or online_lookup._artists_match(fn_info.artist, itunes_info.artist):
                logger.debug(f"[confirmed: filename + musicbrainz] {safe_display(path.name)}")
                return mb_info

    # If fewer than 2 sources confirmed the song: do not guess!
    logger.info(
        f"[unconfirmed] {safe_display(path.name)}: "
        f"could not confirm with at least 2 agreeing sources -> routing to Unrecognized"
    )
    return None


# ── File operations ────────────────────────────────────────────────────────────

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
                src_parent = src.parent
                shutil.move(str(src), str(dest))
                # Prune empty parent folders of the moved source file
                try:
                    curr = src_parent
                    while curr != output_root and curr != curr.parent:
                        if not any(curr.iterdir()):
                            curr.rmdir()
                            curr = curr.parent
                        else:
                            break
                except Exception:
                    pass
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


def organize_unrecognized_file(
    src: Path,
    output_root: Path,
    mode: FileMode = FileMode.COPY,
    dry_run: bool = False,
) -> Optional[Path]:
    """
    Move or copy an unrecognized file into a dedicated 'Unrecognized' folder.
    """
    dest_dir = output_root / "Unrecognized"
    dest = dest_dir / src.name

    if dest == src:
        logger.info(f"[skip] Already in Unrecognized: {src.name}")
        return dest

    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Handle duplicate filenames
        counter = 1
        original_stem = dest.stem
        while dest.exists() and dest.resolve() != src.resolve():
            dest = dest.with_stem(f"{original_stem} ({counter})")
            counter += 1

        try:
            if mode == FileMode.MOVE:
                src_parent = src.parent
                shutil.move(str(src), str(dest))
                # Prune empty parent folders of the moved source file
                try:
                    curr = src_parent
                    while curr != output_root and curr != curr.parent:
                        if not any(curr.iterdir()):
                            curr.rmdir()
                            curr = curr.parent
                        else:
                            break
                except Exception:
                    pass
            else:
                shutil.copy2(str(src), str(dest))
        except Exception as exc:
            logger.error(f"Failed to {mode.value} {src.name} to Unrecognized: {exc}")
            return None

    return dest
