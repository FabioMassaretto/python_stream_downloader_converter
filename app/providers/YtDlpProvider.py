from app.helpers.utils import FileMover
from app.helpers.utils.ApplicationVariables import ApplicationVariables
from app.helpers.utils.QueueUtil import QueueUtil
from app.providers.ProviderBase import ProviderBase
from app.config.LoggerConfig import logging
from yt_dlp import YoutubeDL, DownloadError
from pathlib import Path

logger = logging.getLogger(__name__)


class YtDlpProvider(ProviderBase):
    file_mover: FileMover = FileMover
    __dest_downloaded_video_path__ = ApplicationVariables.get("DEST_DOWNLOADED_VIDEO_PATH")

    ydl_opts = {
        'outtmpl': '%(fulltitle)s.%(ext)s',
        'windowsfilenames': True,
        # 'check_formats': 'selected',
        # 'progress_hooks': [my_hook],
        'paths': {'home': str(__dest_downloaded_video_path__.resolve()) },
        # 'format': 'bv[height>=720]+ba[ext=m4a]/best[height>=720]'
        'format': 'bv*+ba/bestvideo+bestaudio/best', # bv*+ba → flexible matching (not strict filters)
                                                     # bestvideo+bestaudio → fallback merge
                                                     # best → ultimate fallback (guaranteed to work)
    }

    def download(self, urls: list[str]) -> None:
        for url in urls:
            with YoutubeDL(YtDlpProvider.ydl_opts) as ytdlp:
                    try:
                        # Step 1: Extract info BEFORE download to get metadata
                        info = ytdlp.extract_info(url, download=False)

                        # dynamic format selection
                        best_format = self.select_best_format(info.get("formats", []))
                        logger.debug(f"Selected format: {best_format}")

                        ytdlp.params["format"] = best_format

                        # Step 2: Get the actual file name yt_dlp will save to
                        actual_file_path = Path(ytdlp.prepare_filename(info))

                        # Step 3: Download using this info (won’t re-download if already done)
                        ytdlp.download([url])

                        logger.debug(f"Real saved path: {actual_file_path}")
                    except DownloadError as de:
                        logger.error(f'Cannot download: {url} -> {str(de)}')
                        
                        return
                    except Exception as e:
                        logger.error(f'{repr(e)}')

                        return
                    
                    logger.debug(f"Downloaded file: {actual_file_path}")
                    
                    QueueUtil.put_in_queue_list(actual_file_path)

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