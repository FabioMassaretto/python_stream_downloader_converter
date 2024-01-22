from Helpers.Providers.YoutubeProvider import YoutubeProvider


class DownloaderFactory():

    def download(self, provider, link):
        provider_obj = self.__get_source_provider__(provider)
        provider_obj(link)

    def __get_source_provider__(self, provider):
        if provider == 'YOUTUBE':
            return self.__youtube_provider__
        else:
            raise ValueError(provider)
        
    def __youtube_provider__(self, link):
        youtube_provider = YoutubeProvider()
        youtube_provider.download(link)
