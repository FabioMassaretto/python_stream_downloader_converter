import copy
import threading
import concurrent.futures
from pathlib import Path
from typing import List, Optional

from rich.console import Console, Group
from rich.live import Live
from rich.prompt import Prompt
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TaskID,
)
from yt_dlp import YoutubeDL, DownloadError
from yt_dlp.utils import YoutubeDLError
from yt_dlp.networking.impersonate import ImpersonateTarget

from app.helpers.utils import FileMover
from app.helpers.utils.ApplicationVariables import ApplicationVariables
from app.helpers.utils.QueueUtil import QueueUtil
from app.providers.ProviderBase import ProviderBase
from app.config.LoggerConfig import logging, console

try:
    import curl_cffi
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False
    print("Warning: 'curl-cffi' is missing. Impersonation will fail!")

logger = logging.getLogger(__name__)


class YtDlpLogger:
    @staticmethod
    def format_msg(msg: str) -> str:
        # Simplify file deletion messages from yt-dlp postprocessors for clean readability
        if "Deleting original file" in msg:
            parts = msg.split("Deleting original file", 1)[-1].strip()
            if "(pass -k to keep)" in parts:
                file_part = parts.replace("(pass -k to keep)", "").strip()
                filename = Path(file_part).name
                return f"Cleaned up temporary stream: {filename}"
            else:
                filename = Path(parts).name
                return f"Cleaned up temporary stream: {filename}"
        elif "[Merger] Merging formats into" in msg:
            clean_target = msg.replace('[Merger] Merging formats into', '').strip().strip('"').strip("'")
            filename = Path(clean_target).name
            return f"[Merger] Merging streams into: {filename}"
        return msg

    def debug(self, msg: str) -> None:
        if msg.startswith('[download]') or msg.startswith('[frag'):
            return
        logger.debug(self.format_msg(msg))

    def info(self, msg: str) -> None:
        if msg.startswith('[download]') or msg.startswith('[frag'):
            return
        logger.info(self.format_msg(msg))

    def warning(self, msg: str) -> None:
        logger.warning(self.format_msg(msg))

    def error(self, msg: str) -> None:
        logger.error(self.format_msg(msg))


class DownloadTarget:
    def __init__(self, url: str, title: str = ""):
        self.url = url
        self.title = title or url


class YtDlpProvider(ProviderBase):
    file_mover: FileMover = FileMover
    __dest_downloaded_video_path__ = ApplicationVariables.get("DEST_DOWNLOADED_VIDEO_PATH")

    url_tracked_list: list[str] = []
    try_except_count: int = 0

    base_ydl_opts = {
        'outtmpl': '%(fulltitle)s.%(ext)s',
        'windowsfilenames': True,
        'paths': {'home': str(__dest_downloaded_video_path__.resolve())},
        'format': 'bv*+ba/bestvideo+bestaudio/best',
        'concurrent_fragment_downloads': 4,
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
    }

    cookies_file_path = Path(__file__).parent / "cookies" / "www.youtube.com_cookies.txt"

    # Ordered list of extra option overlays to try, one per attempt, when a
    # download fails. Attempt 0 uses base_ydl_opts as-is (no overlay).
    retry_strategies: list[dict] = [
        {},  # first attempt: plain base options
        {'extractor_args': {'youtube': {'player_client': ['android']}}},
        {'impersonate': ImpersonateTarget('edge', os='windows')},
        {'cookiesfrombrowser': ['firefox']},
    ]
    if cookies_file_path.exists():
        retry_strategies.append({'cookiefile': str(cookies_file_path.resolve())})

    def __init__(self, default_max_workers: int = 3):
        self.default_max_workers = default_max_workers

    def download(self, urls: list[str], max_workers: Optional[int] = None) -> None:
        self.__dest_downloaded_video_path__.mkdir(parents=True, exist_ok=True)

        console.print("\n[bold cyan]Preparing and expanding download target(s)...[/bold cyan]")
        targets = self.resolve_targets(urls)

        if not targets:
            console.print("[bold red]No downloadable targets found.[/bold red]")
            return

        total_videos = len(targets)

        if max_workers is None:
            max_workers = self.get_max_workers(total_videos)

        active_workers = min(max_workers, total_videos)
        console.print(
            f"\n[bold]Starting download of [green]{total_videos}[/green] video(s) "
            f"using [cyan]{active_workers}[/cyan] concurrent download thread(s)...[/bold]\n"
        )

        self._download_targets(targets, max_workers=active_workers)

    def get_max_workers(self, target_count: int) -> int:
        if target_count <= 1:
            return 1

        default_workers = min(self.default_max_workers, target_count)
        try:
            choice = Prompt.ask(
                "Concurrent download threads (1-8)",
                default=str(default_workers)
            )
            workers = int(choice)
            return max(1, min(workers, 8))
        except (ValueError, Exception):
            return default_workers

    def resolve_targets(self, urls: list[str]) -> list[DownloadTarget]:
        targets: list[DownloadTarget] = []
        for url in urls:
            url = url.strip()
            if not url:
                continue

            if ('playlist' in url) or ('list=' in url):
                logger.debug(f"Processing playlist URL: {url}")
                playlist_targets = self._resolve_playlist(url)
                if playlist_targets:
                    targets.extend(playlist_targets)
                else:
                    # Fallback to single video URL
                    targets.append(DownloadTarget(url=url))
            else:
                logger.debug(f"Processing single video URL: {url}")
                targets.append(DownloadTarget(url=url))

        return targets

    def _resolve_playlist(self, url: str) -> list[DownloadTarget]:
        targets: list[DownloadTarget] = []
        for attempt, overlay in enumerate(self.retry_strategies):
            ydl_options = copy.deepcopy(self.base_ydl_opts)
            ydl_options.update(copy.deepcopy(overlay))
            ydl_options['extract_flat'] = 'in_playlist'
            ydl_options['logger'] = YtDlpLogger()

            try:
                with YoutubeDL(ydl_options) as ytdlp:
                    info = ytdlp.extract_info(url, download=False)
                    if info and info.get('_type') == 'playlist':
                        entries = info.get('entries') or []
                        for entry in entries:
                            if not entry:
                                continue
                            entry_url = entry.get('webpage_url') or entry.get('url')
                            if not entry_url and entry.get('id'):
                                entry_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                            elif entry_url and not entry_url.startswith("http"):
                                entry_url = f"https://www.youtube.com/watch?v={entry_url}"

                            entry_title = entry.get('title') or entry_url
                            if entry_url:
                                targets.append(DownloadTarget(url=entry_url, title=entry_title))

                        logger.info(f"Resolved {len(targets)} videos from playlist: {url}")
                        return targets
                    elif info and (info.get('webpage_url') or info.get('id')):
                        vid_url = info.get('webpage_url') or f"https://www.youtube.com/watch?v={info.get('id')}"
                        targets.append(DownloadTarget(url=vid_url, title=info.get('title', vid_url)))
                        return targets
            except DownloadError as de:
                logger.warning(f"Playlist extraction attempt {attempt + 1} failed: {str(de)}")
                if attempt < len(self.retry_strategies) - 1:
                    continue
                break
            except Exception as e:
                logger.error(f"Error during playlist extraction: {repr(e)}")
                break

        return targets

    def _download_targets(self, targets: list[DownloadTarget], max_workers: int) -> None:
        total_videos = len(targets)

        overall_progress = Progress(
            TextColumn("[bold yellow]{task.description}[/bold yellow]"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TextColumn("({task.completed:.0f}/{task.total:.0f} completed)"),
            console=console,
        )

        video_progress = Progress(
            SpinnerColumn("line"),
            TextColumn("[cyan]{task.description}[/cyan]", justify="left"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        )

        progress_group = Group(overall_progress, video_progress)
        overall_task = overall_progress.add_task("Overall Progress", total=total_videos)

        with Live(progress_group, console=console, refresh_per_second=10):
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        self._download_single_target,
                        target,
                        video_progress,
                        overall_progress,
                        overall_task,
                    )
                    for target in targets
                ]
                concurrent.futures.wait(futures)

        console.line()

    def _download_single_target(
        self,
        target: DownloadTarget,
        video_progress: Progress,
        overall_progress: Progress,
        overall_task: TaskID,
    ) -> None:
        display_name = target.title if target.title else target.url
        truncated_name = (display_name[:32] + "...") if len(display_name) > 35 else display_name
        task_id = video_progress.add_task(f"[cyan]{truncated_name}[/cyan]", total=None)

        def progress_hook(d: dict):
            status = d.get('status')
            if status == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                fname = Path(d.get('filename', '')).stem
                cur_title = fname if fname else target.title
                trunc = (cur_title[:32] + "...") if len(cur_title) > 35 else cur_title
                video_progress.update(
                    task_id,
                    completed=downloaded,
                    total=total if total > 0 else None,
                    description=f"[cyan]{trunc}[/cyan]"
                )
            elif status == 'finished':
                video_progress.update(task_id, description="[green]Processing / Merging...[/green]")

        download_success = False
        final_file_path: Optional[Path] = None

        for attempt, overlay in enumerate(self.retry_strategies):
            ydl_options = copy.deepcopy(self.base_ydl_opts)
            ydl_options.update(copy.deepcopy(overlay))
            ydl_options['logger'] = YtDlpLogger()
            ydl_options['progress_hooks'] = [progress_hook]

            try:
                with YoutubeDL(ydl_options) as ytdlp:
                    info = ytdlp.extract_info(target.url, download=False)
                    if not info:
                        raise DownloadError(f"Cannot extract info for {target.url}")

                    title = info.get("title", target.title)
                    trunc_title = (title[:32] + "...") if len(title) > 35 else title
                    video_progress.update(task_id, description=f"[cyan]{trunc_title}[/cyan]")

                    best_format = self.select_best_format(info.get("formats", []))
                    logger.debug(f"Selected format for {target.url}: {best_format}")
                    ytdlp.params["format"] = best_format

                    ytdlp.download([target.url])

                    raw_path = Path(ytdlp.prepare_filename(info))
                    actual_file_path = raw_path

                    if not actual_file_path.exists():
                        dest_dir = self.__dest_downloaded_video_path__
                        matches = list(dest_dir.glob(f"{raw_path.stem}.*"))
                        if matches:
                            actual_file_path = matches[0]

                    if actual_file_path.exists():
                        final_file_path = actual_file_path
                        QueueUtil.put_in_queue_list(actual_file_path)
                        logger.info(f"Successfully downloaded: {actual_file_path}")
                        console.print(f"[bold green][OK] Downloaded:[/bold green] {title}")
                        download_success = True
                        break
                    else:
                        logger.warning(f"File not found on disk after download: {raw_path}")

            except DownloadError as de:
                logger.error(f"Cannot download: {target.url} -> {str(de)}")
                if attempt < len(self.retry_strategies) - 1:
                    logger.warning(
                        f"Retrying download for: {target.url} "
                        f"(attempt {attempt + 2}/{len(self.retry_strategies)})"
                    )
                    continue
                else:
                    logger.error(f"All retry strategies exhausted for: {target.url}")
                    console.print(f"[bold red][FAIL] Failed to download:[/bold red] {target.title or target.url}")
                    break
            except YoutubeDLError as yde:
                logger.error(f"YoutubeDL error: {repr(yde)}")
                console.print(f"[bold red][FAIL] YoutubeDL error:[/bold red] {target.title or target.url} - {str(yde)}")
                break
            except Exception as e:
                logger.error(f"Unexpected error downloading {target.url}: {repr(e)}")
                console.print(f"[bold red][FAIL] Error downloading:[/bold red] {target.title or target.url} - {str(e)}")
                break

        video_progress.remove_task(task_id)
        overall_progress.advance(overall_task, 1)

    def handle_playlist(self, url: str) -> None:
        targets = self._resolve_playlist(url)
        if targets:
            self._download_targets(targets, max_workers=self.get_max_workers(len(targets)))
        else:
            self.handle_single_video(url)

    def handle_single_video(self, url: str, preloaded_info: Optional[dict] = None) -> None:
        title = preloaded_info.get('title') if preloaded_info else ""
        targets = [DownloadTarget(url=url, title=title)]
        self._download_targets(targets, max_workers=1)

    def select_best_format(self, formats: list[dict]) -> str:
        video_only = []
        audio_only = []
        progressive = []

        for f in formats:
            if f.get("vcodec") != "none" and f.get("acodec") != "none":
                progressive.append(f)
            elif f.get("vcodec") != "none":
                video_only.append(f)
            elif f.get("acodec") != "none":
                audio_only.append(f)

        def sort_video(f):
            return (
                f.get("height") or 0,
                f.get("tbr") or 0
            )

        def sort_audio(f):
            return f.get("tbr") or 0

        video_only.sort(key=sort_video, reverse=True)
        audio_only.sort(key=sort_audio, reverse=True)
        progressive.sort(key=sort_video, reverse=True)

        # 1. Try best >=720p video + best audio
        for v in video_only:
            if (v.get("height") or 0) >= 720:
                if audio_only:
                    return f"{v['format_id']}+{audio_only[0]['format_id']}"

        # 2. Try best video + best audio (any resolution)
        if video_only and audio_only:
            return f"{video_only[0]['format_id']}+{audio_only[0]['format_id']}"

        # 3. Try best progressive (single file)
        if progressive:
            return progressive[0]["format_id"]

        # 4. Absolute fallback
        return "best"
