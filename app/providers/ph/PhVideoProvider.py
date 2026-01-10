import re
from Helpers.Utils.FileMover import FileMover
from app.helpers.utils.ApplicationVariables import ApplicationVariables
from app.providers.ph.PhDownloaderBase import PhDownloaderBase
from yt_dlp import YoutubeDL
from app.config.LoggerConfig import logging

logger = logging.getLogger(__name__)


class PhVideoProvider(PhDownloaderBase):
    __dest_temp_ph_video_path__ = ApplicationVariables.get("DEST_TEMP_PH_VIDEO_PATH")
    __dest_downloaded_ph_video_path__ = ApplicationVariables.get("DEST_DOWNLOADED_PH_VIDEO_PATH")

    def __init__(self):
        super().__init__()

    def download(self, url: str) -> None:
        options = {
            'outtmpl': f'{self.__dest_temp_ph_video_path__}/%(id)s.%(ext)s',
        }

        # If anyone knows how to mute the output of this send help :,)
        ydl = YoutubeDL(options)
        with ydl:
            try:
                result = ydl.extract_info(
                    url,
                    download=True
                )

                temp_filename = result['id']

                filename = f'{result['uploader']} - {result['title']} - {result['id']}'
                filename = re.sub('[^A-Za-z0-9 ]+', '', filename)
                filename = filename.replace(' ', '-')

                from_temp_path = f"{self.__dest_temp_ph_video_path__}/{temp_filename}.mp4"
                to_final_path = f"{self.__dest_downloaded_ph_video_path__}/{filename}.mp4"
                
                FileMover.copy2(from_temp_path, to_final_path)

            except Exception as e:
                logger.error(f"Exception: {repr(e)}")
