import shutil
from pathlib import Path

from Helpers.Utils.ApplicationVariables import ApplicationVariables
from config.LoggerConfig import logging

logger = logging.getLogger(__name__)


class FileMover:
    QUEUE_VIDEO_PATH = ApplicationVariables().get("QUEUE_VIDEO_PATH")
    
    
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