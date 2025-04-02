import shutil
import os
from pathvalidate import sanitize_filepath
from pathlib import Path

from Helpers.Utils.ApplicationVariables import ApplicationVariables


class FileMover:
    DOWNLOADED_VIDEO_PATH = ApplicationVariables().get("DEST_DOWNLOADED_VIDEO_PATH")
    QUEUE_VIDEO_PATH = ApplicationVariables().get("QUEUE_VIDEO_PATH")
    
    
    @staticmethod
    def move_to_queue_dir(filename):
        download_folder_path = FileMover.DOWNLOADED_VIDEO_PATH
        download_full_path = FileMover.swap_special_character(download_folder_path + filename)
        
        queue_folder_path = FileMover.QUEUE_VIDEO_PATH
        queue_full_path = sanitize_filepath(queue_folder_path + filename)

        is_coppied = FileMover.copy2(download_full_path, queue_full_path)

        print(f"[FileMover] - Moving: Video -> {queue_full_path} was added to the queue.", end='\n') if is_coppied else print('\nMoving: Failed to move to queue! See error above.')


        
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
        
    @staticmethod
    def swap_special_character(path: str) -> str:
        special_characteres = {'*': '＊',}

        # This is a workaround because yt_dlp is changing * (asteristic) to ＊
        for key, value in special_characteres.items():
            path = path.replace(key, value)
            
        return path
        