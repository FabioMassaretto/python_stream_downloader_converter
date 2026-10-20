from abc import ABC, abstractmethod
from pathlib import Path


class AudioConverter(ABC):

    @abstractmethod
    def process_to_extract_audio(
        self,
        video_path_list: list[Path],
        format_type: str = "mp3",
        max_workers: int | None = None,
    ) -> None:
        pass
