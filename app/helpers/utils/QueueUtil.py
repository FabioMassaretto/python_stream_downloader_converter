from pathlib import Path
from typing import List
from app.helpers.utils.FileMover import FileMover
from app.config.LoggerConfig import logging

logger = logging.getLogger(__name__)


class QueueUtil():
    _audio_extract_queue: List[Path] = []

    @classmethod
    def move_video_to_queue_folder(cls, video_path: Path) -> bool:
        logger.debug(f"Moving video to queue folder: {video_path}")
        return FileMover.move_to_queue_dir(video_path)

    @classmethod
    def get_video_in_audio_extract_queue(cls) -> list[Path]:
        logger.debug(f"Getting video files in audio extract queue folder")
        return FileMover.get_queue_dir_file()
    
    @staticmethod
    def put_in_queue_list(path: Path) -> None:
        logger.debug(f"Adding video to audio extract queue list: {path}")
        logger.debug(f"Current queue before adding: {QueueUtil._audio_extract_queue}")
        QueueUtil._audio_extract_queue.append(path)
        logger.debug(f"Updated queue after adding: {QueueUtil._audio_extract_queue}")

    @staticmethod
    def get_queue_list() -> List[Path]:
        logger.debug(f"Retrieving current audio extract queue list: {QueueUtil._audio_extract_queue}")
        return QueueUtil._audio_extract_queue

    @staticmethod
    def remove_from_queue_list(path: Path) -> None:
        logger.debug(f"Removing video from audio extract queue list: {path}")
        logger.debug(f"Current queue before removing: {QueueUtil._audio_extract_queue}")
        if path in QueueUtil._audio_extract_queue:
            QueueUtil._audio_extract_queue.remove(path)
            logger.debug(f"Updated queue after removing: {QueueUtil._audio_extract_queue}")
    