from Helpers.Providers.YtdlpProvider import YtdlpProvider
from Helpers.Providers.Pytube3Provider import Pytube3Provider
from Helpers.Providers.ph.PhProvider import PhProvider
from Helpers.Providers.PytubefixProvider import PytubefixProvider
from Helpers.Providers.SavifyProvider import SavifyProvider
from Helpers.Providers.YoutubeProvider import YoutubeProvider
from config.LoggerConfig import logging

logger = logging.getLogger(__name__)


class DownloaderFactory():

    def create(self, provider):
        return self.__get_download_provider__(provider)

    def __get_download_provider__(self, provider):
        log_selected_option_msg = "Selected option =>"
        if provider == 'YTDLP':
            logger.info(f"{log_selected_option_msg} Download Youtube video (yt_dlp)")
            return YtdlpProvider()
        elif provider == 'YOUTUBE':
            logger.info(f"{log_selected_option_msg} Download Youtube video (pytube)")
            return YoutubeProvider()
        elif provider == 'PYTUBE3':
            logger.info(f"{log_selected_option_msg} Download Youtube video (pytube3)")
            return Pytube3Provider()
        elif provider == 'PYTUBEFIX':
            logger.info(f"{log_selected_option_msg} Download Youtube video (pytubefix)")
            return PytubefixProvider()
        elif provider == 'PHUBE':
            logger.info(f"{log_selected_option_msg} Download PH video and images")
            return PhProvider()
        elif provider == 'SAVIFY':
            logger.info(f"{log_selected_option_msg} Download Spotify music (savify)")
            return SavifyProvider()
        else:
            logger.error(f"{provider} not found!")
            raise ValueError(provider)
        