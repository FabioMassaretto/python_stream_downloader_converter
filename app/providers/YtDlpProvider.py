import copy

from yt_dlp.utils import YoutubeDLError

from app.helpers.utils import FileMover
from app.helpers.utils.ApplicationVariables import ApplicationVariables
from app.helpers.utils.QueueUtil import QueueUtil
from app.providers.ProviderBase import ProviderBase
from app.config.LoggerConfig import logging
from yt_dlp import YoutubeDL, DownloadError
from yt_dlp.networking.impersonate import ImpersonateTarget
from pathlib import Path

try:
    import curl_cffi
except ImportError:
    print("Warning: 'curl-cffi' is missing. Impersonation will fail!")

logger = logging.getLogger(__name__)


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
    }

    # Ordered list of extra option overlays to try, one per attempt, when a
    # download fails. Attempt 0 uses base_ydl_opts as-is (no overlay).
    retry_strategies: list[dict] = [
        {},  # first attempt: plain base options
        {'extractor_args': {'youtube': {'player_client': ['android']}}},
        {'impersonate': ImpersonateTarget('edge', os='windows') },
        {'cookiesfrombrowser': ['firefox']},
        {'cookies ': '/cookies/cookie.txt'},
    ]

    def download(self, urls: list[str]) -> None:
        for url in urls:
            self.ydl_options = {}

            if ('playlist' in url) or ('list=' in url):
                logger.debug(f"Processing playlist URL: {url}")
                self.handle_playlist(url)
            else:
                logger.debug(f"Processing single video URL: {url}")
                self.handle_single_video(url)

    def handle_playlist(self, url: str) -> None:
        for attempt, overlay in enumerate(self.retry_strategies):
            # Fresh copy each attempt so nothing leaks between URLs/attempts.
            ydl_options = copy.deepcopy(self.base_ydl_opts)
            ydl_options.update(copy.deepcopy(overlay))

            try:
                with YoutubeDL(ydl_options) as ytdlp:
                    info = ytdlp.extract_info(url, download=False)

                    if info.get("_type") == "playlist" and info.get("entries"):
                        for entry in info.get("entries"):
                            entry_url = entry.get("webpage_url")
                            logger.debug(f"Processing playlist entry: {entry_url}")
                            self.handle_single_video(entry_url, entry)

            except DownloadError as de:
                logger.error(f'Cannot download: {url} -> {str(de)}')

                if attempt < len(self.retry_strategies) - 1:
                    logger.warning(
                        f"Retrying download for: {url} "
                        f"(attempt {attempt + 2}/{len(self.retry_strategies)})"
                    )
                    continue  # try next strategy for this same URL
                else:
                    logger.error(f"All retry strategies exhausted for: {url}")
                    return  # give up on this URL only, move on to the next one
            except YoutubeDLError as yde:
                logger.error(f'{repr(yde)}')

                return
            except Exception as e:
                logger.error(f'{repr(e)}')

                return

    def handle_single_video(self, url: str) -> None:
        for attempt, overlay in enumerate(self.retry_strategies):
            # Fresh copy each attempt so nothing leaks between URLs/attempts.
            ydl_options = copy.deepcopy(self.base_ydl_opts)
            ydl_options.update(copy.deepcopy(overlay))

            try:
                with YoutubeDL(ydl_options) as ytdlp:
                    info = ytdlp.extract_info(url, download=False)

                    # dynamic format selection
                    # Step 1: Select the best audio and video format based on the extracted info
                    best_format = self.select_best_format(info.get("formats", []))
                    logger.debug(f"Selected format: {best_format}")

                    ytdlp.params["format"] = best_format

                    # Step 2: Download using this info (won’t re-download if already done)
                    ytdlp.download([url])

                    # Step 3: Move the successful downloaded video to the queue folder
                    actual_file_path = Path(ytdlp.prepare_filename(info))
                    logger.debug(f"Video path saved location: {actual_file_path}")
                    QueueUtil.put_in_queue_list(actual_file_path)

            except DownloadError as de:
                logger.error(f'Cannot download: {url} -> {str(de)}')
 
                if attempt < len(self.retry_strategies) - 1:
                    logger.warning(
                        f"Retrying download for: {url} "
                        f"(attempt {attempt + 2}/{len(self.retry_strategies)})"
                    )
                    continue  # try next strategy for this same URL
                else:
                    logger.error(f"All retry strategies exhausted for: {url}")
                    return  # give up on this URL only, move on to the next one
            except YoutubeDLError as yde:
                logger.error(f'{repr(yde)}')

                return
            except Exception as e:
                logger.error(f'{repr(e)}')

                return
            # else:
            #     # Success — record result and stop retrying this URL
            #     logger.debug(f"Downloaded file: {actual_file_path}")
            #     QueueUtil.put_in_queue_list(actual_file_path)
            #     return
            

    def select_best_format(self, formats: list[dict]) -> str:
        # Separate formats
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

        # Sort helpers
        def sort_video(f):
            return (
                f.get("height") or 0,
                f.get("tbr") or 0
            )

        def sort_audio(f):
            return f.get("tbr") or 0

        # Sort descending
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