import shutil
from pathlib import Path

from Helpers.Utils.ApplicationVariables import ApplicationVariables


class FileMover:
    QUEUE_VIDEO_PATH = ApplicationVariables().get("QUEUE_VIDEO_PATH")
    
    
    @staticmethod
    def move_to_queue_dir(from_path: Path):
        queue_folder_path = FileMover.QUEUE_VIDEO_PATH

        to_path = Path(queue_folder_path) / from_path.name

        is_coppied = FileMover.copy2(from_path, to_path)

        if is_coppied:
            print(f"[FileMover] - Moving: Video -> {to_path} was added to the queue.")
        else:
            print("[FileMover] - Failed to move to queue. See error above.")

        
    @staticmethod
    def copy2(from_path: str, to_path: str):
        from_path_converted = Path(from_path)
        to_path_converted = Path(to_path)
        
        if not from_path_converted.exists():   
            print(f"[ERROR][FileMover] - Source file not found: {from_path}")
            return False
        
        try:
            shutil.copy2(from_path_converted, to_path_converted)
            return True
        except Exception as ex:
            print(f'[ERROR][FileMover] - {repr(ex)}')
            return False