from abc import ABC, abstractmethod


class PhDownloaderBase(ABC):
    @abstractmethod
    def download(self, url: str) -> None:
        pass