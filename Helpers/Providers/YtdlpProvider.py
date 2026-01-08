from yt_dlp import YoutubeDL, DownloadError
from pathlib import Path
from Helpers.Utils import InputUtils
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.FileMover import FileMover
from config.LoggerConfig import logging

logger = logging.getLogger(__name__)

class YtdlpProvider:
    file_mover = FileMover()
    __dest_downloaded_video_path__ = ApplicationVariables().get("DEST_DOWNLOADED_VIDEO_PATH")

    def __init__(self):
        link = InputUtils.handle_user_url_input('youtube')

        if InputUtils.is_digit_and_go_back(link):
            return

        self.download(link)
    
    
    ydl_opts = {
        'outtmpl': '%(fulltitle)s.%(ext)s',
        'windowsfilenames': True,
        'check_formats': 'selected',
        # 'progress_hooks': [my_hook],
        'paths': {'home': __dest_downloaded_video_path__ },
        'format': 'bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
        # 'format': "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        # 'format': "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba) / (bv*+ba/b)",
        # 'format': "bestvideo[height>=720]best[ext=mp4]",
    }
    
    def download(self, link, opt=ydl_opts):
            with YoutubeDL(opt) as ytdlp:
                try:
                    # Step 1: Extract info BEFORE download to get metadata
                    info = ytdlp.extract_info(link, download=False)

                    # Step 2: Get the actual file name yt_dlp will save to
                    actual_file_path = Path(ytdlp.prepare_filename(info))

                    # Step 3: Download using this info (won’t re-download if already done)
                    ytdlp.download(link)

                    logger.debug(f"Real saved path: {actual_file_path}")
                except DownloadError as de:
                    logger.error(f'Cannot download: {link} -> {str(de)}')
                    
                    return
                except Exception as e:
                    logger.error(f'{repr(e)}')

                    return
                
            logger.debug(f"Downloaded file: {actual_file_path}")
                
            # info = ytdlp.extract_info(link, download=False)
            YtdlpProvider.queue_for_audio_extraction(actual_file_path)
          
            
    @staticmethod
    def queue_for_audio_extraction(filename):
        print('\n\n                 ------------------ Queue for audio extraction --------------------------                 ')
        convert_answer = input(f"Do you want to queue '{filename}' for audio extraction? (yes(y) or no(n)): ")
            
        while convert_answer not in ("yes", "y", "no", "n"):
            convert_answer = input(
                f"Invalid answer. Do you want to queue '{filename}' for audio extraction? yes(y) or no(n): ")
        else:
            if convert_answer in ("no", "n"):
                return

            FileMover.move_to_queue_dir(filename)
