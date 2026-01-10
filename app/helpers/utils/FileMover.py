import shutil
from pathlib import Path

from app.helpers.utils.ApplicationVariables import ApplicationVariables
from app.config.LoggerConfig import logging

logger = logging.getLogger(__name__)


class FileMover():
    QUEUE_VIDEO_PATH = ApplicationVariables.get("QUEUE_VIDEO_PATH")
    VALID_VIDEO_EXTENSIONS = ApplicationVariables.get("ALLOWED_FILE_EXTENSIONS")
    
    
    @staticmethod
    def move_to_queue_dir(from_path: Path):
        queue_folder_path = FileMover.QUEUE_VIDEO_PATH

        to_path = Path(queue_folder_path) / from_path.name

        is_coppied = FileMover.copy2(from_path, to_path)

        print("\n")

        if is_coppied:
            logger.info(f"Moving video {to_path} to the queue.")
        else:
            logger.error("It wans't possible to move to queue. See error above.")
    
    @staticmethod
    def get_queue_dir_file() -> list[Path]:
        return [p for p in Path(FileMover.QUEUE_VIDEO_PATH).iterdir() if p.is_file() and (p.suffix in FileMover.VALID_VIDEO_EXTENSIONS)]
        
    @staticmethod
    def copy2(from_path: str, to_path: str):
        from_path_converted = Path(from_path)
        to_path_converted = Path(to_path)
        
        if not from_path_converted.exists():   
            logger.error(f"Source file: {from_path} not found!")

            return False
        
        try:
            shutil.copy2(from_path_converted, to_path_converted)

            return True
        except Exception as ex:
            logger.error(f"{repr(ex)}")

            return False