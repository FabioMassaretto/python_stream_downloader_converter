from pathlib import Path
from app.helpers.utils.FileMover import FileMover
from app.ui.menu import is_video_to_audio_extract_queued


class QueueUtil():
    _audio_extract_queue: list[str] = []

    @classmethod
    def put_video_in_audio_extract_queue(cls, video_path: str) -> None:
        if is_video_to_audio_extract_queued(video_path):
            FileMover.move_to_queue_dir(video_path)

    @classmethod
    def get_video_in_audio_extract_queue(cls) -> list[Path]:
        return FileMover.get_queue_dir_file()