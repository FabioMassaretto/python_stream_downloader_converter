import concurrent.futures
import os
import threading
from pathlib import Path

from pydub import AudioSegment
from rich.console import Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from app.config.LoggerConfig import console, logging
from app.converters.audio.AudioConverter import AudioConverter
from app.helpers.utils.ApplicationVariables import ApplicationVariables
from app.helpers.utils.FileMover import FileMover

logger = logging.getLogger(__name__)

# Pydub's AudioSegment is not thread-safe when writing to the same file
# but parallel reads + independent writes are fine. Use a lock only for
# the shared counter.
_counter_lock = threading.Lock()


class PydubConverter(AudioConverter):
    dest_converted_audio_path = ApplicationVariables.get("DEST_CONVERTED_AUDIO_PATH")
    queue_video_path = ApplicationVariables.get("QUEUE_VIDEO_PATH")

    def __init__(self):
        logger.info("Selected => Convert a Youtube video to audio file")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process_to_extract_audio(
        self,
        videos_path: list[Path],
        format_type: str = "mp3",
        max_workers: int | None = None,
    ) -> None:
        if not videos_path:
            console.print("[yellow]No videos to convert.[/yellow]")
            return

        if max_workers is None:
            max_workers = os.cpu_count() or 4

        active_workers = min(max_workers, len(videos_path))
        console.print(
            f"\n[bold]Starting audio extraction of [green]{len(videos_path)}[/green] "
            f"file(s) using [cyan]{active_workers}[/cyan] thread(s)...[/bold]\n"
        )

        self._convert_parallel(videos_path, format_type, max_workers=active_workers)

    # ------------------------------------------------------------------
    # Progress UI + ThreadPoolExecutor
    # ------------------------------------------------------------------

    def _convert_parallel(
        self,
        videos_path: list[Path],
        format_type: str,
        max_workers: int,
    ) -> None:
        total = len(videos_path)
        quantity_converted = 0

        overall_progress = Progress(
            TextColumn("[bold yellow]{task.description}[/bold yellow]"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TextColumn("({task.completed:.0f}/{task.total:.0f} completed)"),
            console=console,
        )

        file_progress = Progress(
            SpinnerColumn("line"),
            TextColumn("[cyan]{task.description}[/cyan]", justify="left"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            console=console,
        )

        progress_group = Group(overall_progress, file_progress)
        overall_task = overall_progress.add_task("Overall Progress", total=total)

        with Live(progress_group, console=console, refresh_per_second=10):
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_path = {
                    executor.submit(
                        self._convert_single,
                        video_path,
                        format_type,
                        file_progress,
                        overall_progress,
                        overall_task,
                    ): video_path
                    for video_path in videos_path
                }

                for future in concurrent.futures.as_completed(future_to_path):
                    video_path = future_to_path[future]
                    try:
                        success = future.result()
                        if success:
                            with _counter_lock:
                                quantity_converted += 1
                    except Exception as e:
                        logger.error(f"Unexpected error converting {video_path.name}: {repr(e)}")

        console.line()

        ending = "s" if quantity_converted != 1 else ""
        console.print(
            f"[bold]Converted [green]{quantity_converted}[/green] of "
            f"[cyan]{total}[/cyan] file{ending}.[/bold]"
        )

    # ------------------------------------------------------------------
    # Per-file conversion (runs inside a worker thread)
    # ------------------------------------------------------------------

    def _convert_single(
        self,
        video_path: Path,
        format_type: str,
        file_progress: Progress,
        overall_progress: Progress,
        overall_task: TaskID,
    ) -> bool:
        full_from_path = self.queue_video_path / video_path.name
        full_dest_path = self.dest_converted_audio_path / f"{video_path.stem}.{format_type}"

        display_name = video_path.stem
        trunc = (display_name[:32] + "...") if len(display_name) > 35 else display_name
        task_id = file_progress.add_task(f"[cyan]{trunc}[/cyan]", total=None)

        logger.info(f"Converting: {video_path.name} ...")

        try:
            file_progress.update(task_id, description=f"[cyan]{trunc}[/cyan] — loading")
            audio = AudioSegment.from_file(full_from_path)

            file_progress.update(
                task_id,
                description=f"[cyan]{trunc}[/cyan] — exporting",
                total=100,
                completed=50,
            )
            self.dest_converted_audio_path.mkdir(parents=True, exist_ok=True)
            audio.export(full_dest_path, format=format_type)

            file_progress.update(task_id, completed=100)

            # Remove the queue copy
            try:
                FileMover.remove(full_from_path)
            except Exception as rm_err:
                logger.warning(f"Could not remove queue file {full_from_path.name}: {repr(rm_err)}")

            console.print(f"[bold green][OK] Converted:[/bold green] {video_path.name}")
            logger.info(f"Converted: {full_dest_path.name}")
            return True

        except FileNotFoundError as fnfe:
            logger.error(f"File not found: {full_from_path} — {repr(fnfe)}")
            console.print(f"[bold red][FAIL] File not found:[/bold red] {video_path.name}")
            return False
        except Exception as e:
            logger.error(f"Error converting {video_path.name}: {repr(e)}")
            console.print(f"[bold red][FAIL] Conversion error:[/bold red] {video_path.name} — {e}")
            return False
        finally:
            file_progress.remove_task(task_id)
            overall_progress.advance(overall_task, 1)
