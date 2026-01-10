from abc import ABC, abstractmethod
from pathlib import Path


class AudioConverter(ABC):
     
    @abstractmethod
    def process_to_extract_audio(video_path_list: list[Path]):
        pass
