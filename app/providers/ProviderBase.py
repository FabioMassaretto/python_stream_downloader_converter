from abc import ABC, abstractmethod


class ProviderBase(ABC):

    @abstractmethod
    def download(self, urls: list[str]) -> None:
        pass