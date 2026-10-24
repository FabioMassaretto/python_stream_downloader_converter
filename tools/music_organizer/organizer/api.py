"""
Programmatic API for the music organizer.

This module provides a simple function that can be called from other
Python code (i.e. the main downloader app) without going through argparse.
"""
import concurrent.futures
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console, Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from tools.music_organizer.organizer.models import SongInfo
from tools.music_organizer.organizer.utils import safe_display
from tools.music_organizer.organizer.file_organizer import FileMode, organize_file, resolve_metadata
from tools.music_organizer.organizer.scanner import scan

logger = logging.getLogger(__name__)


def organize_directory(
    input_dir: Path,
    output_dir: Optional[Path] = None,
    mode: str = "copy",
    use_online: bool = True,
    max_workers: Optional[int] = None,
    recursive: bool = True,
    dry_run: bool = False,
    console: Optional[Console] = None,
) -> dict:
    """
    Scan *input_dir* for audio files, resolve metadata, and organise them
    into artist/album/title folders under *output_dir*.

    Parameters
    ----------
    input_dir : Path
        Directory containing audio files to organise.
    output_dir : Path or None
        Destination root. Defaults to ``input_dir / "organized"``.
    mode : str
        ``"copy"`` or ``"move"``.
    use_online : bool
        Whether to use MusicBrainz / AcoustID for metadata resolution.
    max_workers : int or None
        Number of parallel threads. Defaults to ``os.cpu_count()``.
    recursive : bool
        Recurse into sub-directories.
    dry_run : bool
        Preview only, do not touch files.
    console : Console or None
        Rich Console to use. Creates one if None.

    Returns
    -------
    dict with keys ``"ok"``, ``"unresolved"``, ``"errors"`` (each a list).
    """
    if console is None:
        console = Console(highlight=False, emoji=False, legacy_windows=False)

    input_dir = Path(input_dir).resolve()
    output_dir = Path(output_dir).resolve() if output_dir else input_dir / "organized"
    file_mode = FileMode(mode)
    workers = max_workers or os.cpu_count() or 4

    # Exclude output_dir from scan to avoid re-organising already organised files
    exclude = []
    try:
        if output_dir.is_relative_to(input_dir):
            exclude.append(output_dir)
    except Exception:
        pass

    files = scan(input_dir, recursive=recursive, exclude_dirs=exclude)

    result = {"ok": [], "unresolved": [], "errors": []}

    if not files:
        logger.info("Music Organizer: no audio files found to organize.")
        console.print("[yellow]Music Organizer: no audio files found to organize.[/yellow]")
        return result

    active_workers = min(workers, len(files))
    console.print(
        f"\n[bold cyan]Music Organizer:[/bold cyan] "
        f"Found [green]{len(files)}[/green] audio file(s). "
        f"Organising with [cyan]{active_workers}[/cyan] thread(s)..."
        + (" [bold red](DRY RUN)[/bold red]" if dry_run else "")
    )

    overall_progress = Progress(
        TextColumn("[bold yellow]{task.description}[/bold yellow]"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        TextColumn("({task.completed:.0f}/{task.total:.0f})"),
        console=console,
    )
    file_progress = Progress(
        SpinnerColumn("line"),
        TextColumn("[cyan]{task.description}[/cyan]", justify="left"),
        TimeRemainingColumn(),
        console=console,
    )

    overall_task = overall_progress.add_task("Organising", total=len(files))

    with Live(
        Group(overall_progress, file_progress),
        console=console,
        refresh_per_second=10,
    ):
        with concurrent.futures.ThreadPoolExecutor(max_workers=active_workers) as executor:
            future_to_path = {
                executor.submit(
                    _process_one,
                    f, output_dir, file_mode, use_online, dry_run,
                    file_progress, overall_progress, overall_task, console,
                ): f
                for f in files
            }
            for future in concurrent.futures.as_completed(future_to_path):
                src = future_to_path[future]
                display = safe_display(src.name)
                try:
                    src, info, dest, status = future.result()
                    if status == "ok":
                        result["ok"].append((src, info, dest))
                    elif status == "unresolved":
                        result["unresolved"].append((src, info))
                    else:
                        result["errors"].append((src,))
                except Exception as exc:
                    logger.error(f"Organizer worker error for {display}: {exc}")
                    result["errors"].append((src,))

    console.line()

    ok_n = len(result["ok"])
    un_n = len(result["unresolved"])
    er_n = len(result["errors"])
    console.print(
        f"[bold cyan]Music Organizer done:[/bold cyan] "
        f"[green]{ok_n} organised[/green]  "
        f"[yellow]{un_n} unresolved[/yellow]  "
        f"[red]{er_n} errors[/red]"
    )

    return result


def organize_files(
    files: list[Path],
    output_dir: Path,
    mode: str = "copy",
    use_online: bool = True,
    max_workers: Optional[int] = None,
    dry_run: bool = False,
    console: Optional[Console] = None,
) -> dict:
    """
    Organise a specific list of audio files (not a directory scan).
    Useful for organising freshly-converted files immediately.

    Same return format as ``organize_directory``.
    """
    from organizer.scanner import AUDIO_EXTENSIONS

    if console is None:
        console = Console(highlight=False, emoji=False, legacy_windows=False)

    output_dir = Path(output_dir).resolve()
    file_mode = FileMode(mode)
    workers = max_workers or os.cpu_count() or 4

    # Filter to audio only
    audio_files = [
        f for f in files
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
    ]

    result = {"ok": [], "unresolved": [], "errors": []}

    if not audio_files:
        return result

    active_workers = min(workers, len(audio_files))
    console.print(
        f"\n[bold cyan]Music Organizer:[/bold cyan] "
        f"Organising [green]{len(audio_files)}[/green] file(s)..."
    )

    overall_progress = Progress(
        TextColumn("[bold yellow]{task.description}[/bold yellow]"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        TextColumn("({task.completed:.0f}/{task.total:.0f})"),
        console=console,
    )
    file_progress = Progress(
        SpinnerColumn("line"),
        TextColumn("[cyan]{task.description}[/cyan]", justify="left"),
        TimeRemainingColumn(),
        console=console,
    )

    overall_task = overall_progress.add_task("Organising", total=len(audio_files))

    with Live(
        Group(overall_progress, file_progress),
        console=console,
        refresh_per_second=10,
    ):
        with concurrent.futures.ThreadPoolExecutor(max_workers=active_workers) as executor:
            future_to_path = {
                executor.submit(
                    _process_one,
                    f, output_dir, file_mode, use_online, dry_run,
                    file_progress, overall_progress, overall_task, console,
                ): f
                for f in audio_files
            }
            for future in concurrent.futures.as_completed(future_to_path):
                src = future_to_path[future]
                display = safe_display(src.name)
                try:
                    src, info, dest, status = future.result()
                    if status == "ok":
                        result["ok"].append((src, info, dest))
                    elif status == "unresolved":
                        result["unresolved"].append((src, info))
                    else:
                        result["errors"].append((src,))
                except Exception as exc:
                    logger.error(f"Organizer worker error for {display}: {exc}")
                    result["errors"].append((src,))

    console.line()

    ok_n = len(result["ok"])
    un_n = len(result["unresolved"])
    er_n = len(result["errors"])
    console.print(
        f"[bold cyan]Music Organizer done:[/bold cyan] "
        f"[green]{ok_n} organised[/green]  "
        f"[yellow]{un_n} unresolved[/yellow]  "
        f"[red]{er_n} errors[/red]"
    )

    return result


# ── Internal worker ───────────────────────────────────────────────────────────

def _process_one(
    src: Path,
    output_dir: Path,
    mode: FileMode,
    use_online: bool,
    dry_run: bool,
    file_progress: Progress,
    overall_progress: Progress,
    overall_task,
    console: Console,
) -> tuple[Path, Optional[SongInfo], Optional[Path], str]:
    display = safe_display(src.name)
    task = file_progress.add_task(f"{display}", total=None)

    try:
        info = resolve_metadata(src, use_online=use_online)

        if not info or not info.is_organizable:
            console.print(f"[yellow][SKIP][/yellow] Unresolved: {display}")
            return src, info, None, "unresolved"

        dest = organize_file(src, info, output_dir, mode=mode, dry_run=dry_run)

        if dest is None:
            console.print(f"[bold red][FAIL][/bold red] {display}")
            return src, info, None, "error"

        verb = "Would copy" if dry_run else mode.value.capitalize() + "d"
        console.print(f"[bold green][OK][/bold green] {verb}: {display}")
        return src, info, dest, "ok"

    except Exception as exc:
        logger.error(f"{src.name}: {exc}")
        console.print(f"[bold red][FAIL][/bold red] {display}: {exc}")
        return src, None, None, "error"
    finally:
        file_progress.remove_task(task)
        overall_progress.advance(overall_task, 1)
