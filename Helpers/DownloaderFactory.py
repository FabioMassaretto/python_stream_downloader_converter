from Helpers.Providers.YtdlpProvider import YtdlpProvider
from Helpers.Providers.Pytube3Provider import Pytube3Provider
from Helpers.Providers.ph.PhProvider import PhProvider
from Helpers.Providers.PytubefixProvider import PytubefixProvider
from Helpers.Providers.SavifyProvider import SavifyProvider
from Helpers.Providers.YoutubeProvider import YoutubeProvider


class DownloaderFactory():

    def create(self, provider):
        return self.__get_download_provider__(provider)

    def __get_download_provider__(self, provider):
        if provider == 'YTDLP':
            return YtdlpProvider()
        elif provider == 'YOUTUBE':
            return YoutubeProvider()
        elif provider == 'PYTUBE3':
            return Pytube3Provider()
        elif provider == 'PYTUBEFIX':
            return PytubefixProvider()
        elif provider == 'PHUBE':
            return PhProvider()
        elif provider == 'SAVIFY':
            return SavifyProvider()
        else:
            raise ValueError(provider)
