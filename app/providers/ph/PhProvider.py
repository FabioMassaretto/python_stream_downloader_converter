from app.helpers.utils.ApplicationVariables import ApplicationVariables
from app.helpers.utils.ValidatorUtil import ValidatorUtil
from app.providers.ProviderBase import ProviderBase
from app.providers.ph.PhPhotoDownloader import PhPhotoDownloader
from app.providers.ph.PhDownloaderBase import PhDownloaderBase
from app.providers.ph.PhVideoDownloader import PhVideoDownloader

class PhProvider(ProviderBase):
    def __init__(self):
        super().__init__()

    def download(self, urls: list[str]) -> list[str]:
        ph_provider: PhDownloaderBase = None

        for url in urls:
            if ValidatorUtil.is_ph_video_url(url):
                ph_provider = PhVideoDownloader()
            elif ValidatorUtil.is_ph_album_url(url):
                ph_provider = PhPhotoDownloader()    

            if ph_provider is None:
                continue
            
            ph_provider.download(url)