from app.providers.ph.PhDownloaderBase import PhDownloaderBase


class PhAlbumProvider(PhDownloaderBase):
    def __init__(self):
        super().__init__()

    def download(self, urls: str) -> None:
        # Implement download logic for PhAlbumProvider here
        pass
