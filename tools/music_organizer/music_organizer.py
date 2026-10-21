#!/usr/bin/env python3
"""
music_organizer.py – standalone music cataloguing & organizer
=============================================================

Scans a directory for audio files, resolves metadata (embedded tags,
AcoustID fingerprint, MusicBrainz lookup, filename parsing) and
organises them into:

    <output>/<Artist>/<Album>/<NN - Title>.ext

Usage
-----
    python music_organizer.py <input_dir>
    python music_organizer.py <input_dir> --output /path/to/library
    python music_organizer.py <input_dir> --mode move --dry-run
    python music_organizer.py <input_dir> --no-online --workers 4

Options
-------
    --output / -o       Destination root  [default: <input>/organized]
    --mode              copy | move       [default: copy]
    --dry-run / -n      Preview only, do not touch files
    --no-online         Skip internet lookup (tags + filename only)
    --workers / -j      Parallel worker threads  [default: cpu_count]
    --no-recursive      Do not recurse into sub-directories
    --log-level         DEBUG | INFO | WARNING | ERROR  [default: INFO]
"""

import argparse
import concurrent.futures
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text

# ── Make the package importable when run as a script ──────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from organizer.scanner import scan
from organizer.models import SongInfo
from organizer.file_organizer import FileMode, organize_file, resolve_metadata

console = Console(highlight=False, emoji=False, legacy_windows=False)


# ── Logging setup ─────────────────────────────────────────────────────────────

def setup_logging(level_name: str) -> None:
    from rich.logging import RichHandler

    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, show_path=False, markup=False)],
    )
    # Silence noisy third-party loggers
    for noisy in ("musicbrainzngs", "urllib3", "requests"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ── Worker: process one file ──────────────────────────────────────────────────

def process_file(
    src: Path,
    output_root: Path,
    mode: FileMode,
    use_online: bool,
    dry_run: bool,
    file_progress: Progress,
    overall_progress: Progress,
    overall_task,
) -> tuple[Path, Optional[SongInfo], Optional[Path], str]:
    """
    Returns (src, info, dest, status)  where status is one of:
        "ok" | "skipped" | "unresolved" | "error"
    """
    display = (src.name[:40] + "...") if len(src.name) > 43 else src.name
    task = file_progress.add_task(f"[cyan]{display}[/cyan]", total=None)

    try:
        info = resolve_metadata(src, use_online=use_online)

        if not info or not info.is_organizable:
            file_progress.update(task, description=f"[yellow]{display}[/yellow]")
            return src, info, None, "unresolved"

        dest = organize_file(src, info, output_root, mode=mode, dry_run=dry_run)

        if dest is None:
            return src, info, None, "error"

        return src, info, dest, "ok"

    except Exception as exc:
        logging.getLogger(__name__).error(f"{src.name}: {exc}")
        return src, info if "info" in dir() else None, None, "error"  # type: ignore
    finally:
        file_progress.remove_task(task)
        overall_progress.advance(overall_task, 1)


# ── Result table ──────────────────────────────────────────────────────────────

def print_summary(
    results: list[tuple[Path, Optional[SongInfo], Optional[Path], str]],
    mode: FileMode,
    dry_run: bool,
) -> None:
    ok         = [r for r in results if r[3] == "ok"]
    unresolved = [r for r in results if r[3] == "unresolved"]
    errors     = [r for r in results if r[3] == "error"]

    action = f"{'Would ' if dry_run else ''}{mode.value.capitalize()}"

    table = Table(
        title=f"Music Organizer — {len(results)} file(s) processed",
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    table.add_column("File", style="dim", no_wrap=False, ratio=3)
    table.add_column("Resolved as", no_wrap=False, ratio=4)
    table.add_column("Destination", no_wrap=False, ratio=5)
    table.add_column("Status", justify="center", ratio=1)

    for src, info, dest, status in sorted(results, key=lambda r: r[0].name.lower()):
        if status == "ok":
            dest_str = str(dest.relative_to(dest.parents[2])) if dest else ""
            table.add_row(
                src.name,
                str(info),
                dest_str,
                f"[green]{action}[/green]",
            )
        elif status == "unresolved":
            table.add_row(src.name, "—", "left in place", "[yellow]Skipped[/yellow]")
        else:
            table.add_row(src.name, "—", "—", "[red]Error[/red]")

    console.print()
    console.print(table)
    console.print()
    console.print(
        f"[bold green]{len(ok)} organised[/bold green]  "
        f"[yellow]{len(unresolved)} unresolved[/yellow]  "
        f"[red]{len(errors)} errors[/red]"
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="music_organizer",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Directory to scan for audio files")
    parser.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Destination root  [default: <input>/organized]",
    )
    parser.add_argument(
        "--mode", choices=["copy", "move"], default="copy",
        help="Whether to copy or move files  [default: copy]",
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Preview what would happen without touching files",
    )
    parser.add_argument(
        "--no-online", action="store_true",
        help="Disable internet lookup (use tags + filename only)",
    )
    parser.add_argument(
        "--workers", "-j", type=int, default=None,
        help="Parallel threads  [default: cpu_count]",
    )
    parser.add_argument(
        "--no-recursive", action="store_true",
        help="Do not recurse into sub-directories",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    args = parser.parse_args()

    setup_logging(args.log_level)
    log = logging.getLogger(__name__)

    input_dir: Path = args.input.resolve()
    if not input_dir.is_dir():
        console.print(f"[bold red]Error:[/bold red] {input_dir} is not a directory.")
        sys.exit(1)

    output_root: Path = (
        args.output.resolve() if args.output else input_dir / "organized"
    )
    mode      = FileMode(args.mode)
    use_online = not args.no_online
    workers   = args.workers or os.cpu_count() or 4
    recursive = not args.no_recursive
    dry_run   = args.dry_run

    # ── Scan ──────────────────────────────────────────────────────────────────
    console.print(
        Panel.fit(
            f"[bold cyan]Music Organizer[/bold cyan]\n\n"
            f"  Input   : [green]{input_dir}[/green]\n"
            f"  Output  : [green]{output_root}[/green]\n"
            f"  Mode    : [yellow]{mode.value}[/yellow]"
            + ("  [bold red](DRY RUN)[/bold red]" if dry_run else "") + "\n"
            f"  Online  : {'yes' if use_online else 'no'}\n"
            f"  Workers : {workers}",
            title="Configuration",
            padding=(1, 4),
        )
    )

    files = scan(input_dir, recursive=recursive)

    if not files:
        console.print("[yellow]No audio files found.[/yellow]")
        return

    console.print(f"\nFound [bold]{len(files)}[/bold] audio file(s). Starting...\n")

    # ── Progress UI ───────────────────────────────────────────────────────────
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

    overall_task = overall_progress.add_task("Processing", total=len(files))
    results: list[tuple[Path, Optional[SongInfo], Optional[Path], str]] = []

    with Live(Group(overall_progress, file_progress), console=console, refresh_per_second=10):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    process_file,
                    f,
                    output_root,
                    mode,
                    use_online,
                    dry_run,
                    file_progress,
                    overall_progress,
                    overall_task,
                ): f
                for f in files
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    src, info, dest, status = result
                    if status == "ok":
                        verb = "Would copy" if dry_run else mode.value.capitalize() + "d"
                        console.print(f"[bold green][OK][/bold green] {verb}: [dim]{src.name}[/dim]")
                    elif status == "unresolved":
                        console.print(f"[yellow][SKIP][/yellow] Unresolved: [dim]{src.name}[/dim]")
                    else:
                        console.print(f"[bold red][FAIL][/bold red] {src.name}")
                except Exception as exc:
                    src = futures[future]
                    log.error(f"Worker crashed for {src.name}: {exc}")
                    results.append((src, None, None, "error"))

    console.line()
    print_summary(results, mode, dry_run)


if __name__ == "__main__":
    main()
