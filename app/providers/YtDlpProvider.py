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
        'check_formats': 'selected',
        # 'progress_hooks': [my_hook],
        'paths': {'home': __dest_downloaded_video_path__ },
        'format': 'bv[height>=720]+ba[ext=m4a]/best[height>=720]'
    }

    def download(self, urls: list[str]) -> None:
        for url in urls:
            with YoutubeDL(YtDlpProvider.ydl_opts) as ytdlp:
                    try:
                        # Step 1: Extract info BEFORE download to get metadata
                        info = ytdlp.extract_info(url, download=False)

                        # Step 2: Get the actual file name yt_dlp will save to
                        actual_file_path = Path(ytdlp.prepare_filename(info))

                        # Step 3: Download using this info (won’t re-download if already done)
                        ytdlp.download(url)

                        logger.debug(f"Real saved path: {actual_file_path}")
                    except DownloadError as de:
                        logger.error(f'Cannot download: {url} -> {str(de)}')
                        
                        return
                    except Exception as e:
                        logger.error(f'{repr(e)}')

                        return
                    
                    logger.debug(f"Downloaded file: {actual_file_path}")
                    
                    QueueUtil.put_video_in_audio_extract_queue(actual_file_path)

