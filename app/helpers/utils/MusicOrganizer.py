"""
Integration between the main app and the standalone music organizer tool.

Adds the organizer's package to sys.path so it can be imported
from anywhere in the app, and provides convenience functions.
"""
import sys
from pathlib import Path
from typing import Optional
from tools.music_organizer.organizer.api import organize_directory, organize_files
from app.helpers.utils.ApplicationVariables import ApplicationVariables  # noqa: E402
from app.config.LoggerConfig import logging, console  # noqa: E402

# Ensure project root and organizer root are in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_ORGANIZER_ROOT = _PROJECT_ROOT / "tools" / "music_organizer"
if str(_ORGANIZER_ROOT) not in sys.path:
    sys.path.insert(0, str(_ORGANIZER_ROOT))


logger = logging.getLogger(__name__)


_CONVERTED_AUDIO_PATH = ApplicationVariables.get("DEST_CONVERTED_AUDIO_PATH")
_DOWNLOADED_VIDEO_PATH = ApplicationVariables.get("DEST_DOWNLOADED_VIDEO_PATH")


def organize_converted_audio(
    output_dir: Optional[Path] = None,
    mode: str = "move",
    use_online: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Scan the converted audio folder and organise all audio files
    into artist/album/title folders.

    By default uses **move** mode so files are relocated, not copied.
    Output defaults to ``<converted_audio_path>/organized``.
    """
    input_dir = _CONVERTED_AUDIO_PATH
    if output_dir is None:
        output_dir = input_dir / "organized"

    input_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Organising converted audio from: {input_dir}")
    return organize_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        mode=mode,
        use_online=use_online,
        dry_run=dry_run,
        console=console,
    )


def organize_specific_files(
    files: list[Path],
    output_dir: Optional[Path] = None,
    mode: str = "copy",
    use_online: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Organise a specific list of files (e.g. freshly converted ones).
    Output defaults to ``<converted_audio_path>/organized``.
    """
    if output_dir is None:
        output_dir = _CONVERTED_AUDIO_PATH / "organized" / "library"

    return organize_files(
        files=files,
        output_dir=output_dir,
        mode=mode,
        use_online=use_online,
        dry_run=dry_run,
        console=console,
    )


if __name__ == "__main__":
    console.print("[bold cyan]MusicOrganizer helper module initialized successfully.[/bold cyan]")
    console.print(f"Project root: {_PROJECT_ROOT}")
    console.print(f"Organizer root: {_ORGANIZER_ROOT}")
    console.print(f"Converted audio path: {_CONVERTED_AUDIO_PATH}")
