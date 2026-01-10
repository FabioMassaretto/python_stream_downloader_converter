from abc import ABC, abstractmethod


class ProviveBase(ABC):

    @abstractmethod
    def download(self, urls: list[str]) -> None:
        pass