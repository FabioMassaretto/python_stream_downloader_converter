from Helpers.Providers.YoutubeProvider import YoutubeProvider


class DownloaderFactory():

    def create(self, provider):
        return self.__get_download_provider__(provider)

    def __get_download_provider__(self, provider):
        if provider == 'YOUTUBE':
            return YoutubeProvider()
        else:
            raise ValueError(provider)