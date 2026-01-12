from abc import ABC
from pathlib import Path
from app.converters.audio.AudioConverter import AudioConverter


class AudioExtractor(ABC):

    def __init__(self, converter: AudioConverter):
        super().__init__()
        self.converter = converter

    
    def extract_audio(self, video_path_list: list[Path]):
        return self.converter.process_to_extract_audio(video_path_list)