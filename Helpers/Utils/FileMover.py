import shutil
import os
from pathlib import Path

from Helpers.Utils.ApplicationVariables import ApplicationVariables


class FileMover:
    DOWNLOADED_VIDEO_PATH = ApplicationVariables().get("DEST_DOWNLOADED_VIDEO_PATH")
    QUEUE_VIDEO_PATH = ApplicationVariables().get("QUEUE_VIDEO_PATH")
    
    @staticmethod
    def rename_downloaded_file(temp_video_filename, final_video_filename):
        downloaded_folder_path = FileMover.DOWNLOADED_VIDEO_PATH
        temp_filename = Path(temp_video_filename).name
        full_path_old_name = downloaded_folder_path + temp_filename
        full_path_new_name = downloaded_folder_path + final_video_filename
        
        try:
            FileMover.__rename_file__(full_path_old_name, full_path_new_name)
            
            print(f"[FileMover] - Renaming: Video was renamed from '{temp_video_filename}' to '{final_video_filename}'.", end='\n') 

        except PermissionError as pe:
            print(f'[ERROR][FileMover] - {repr(pe)}')
        except FileExistsError | FileNotFoundError as fe:
            print(f'[ERROR][FileMover] - {repr(fe)}')
        except Exception as e:
            print(f'[ERROR][FileMover] - {repr(e)}')
    
    
    @staticmethod
    def move_to_queue_dir(filename):
        download_folder_path = FileMover.DOWNLOADED_VIDEO_PATH
        download_full_path = download_folder_path + filename
        
        queue_folder_path = FileMover.QUEUE_VIDEO_PATH
        queue_full_path = queue_folder_path + filename

        is_coppied = FileMover.copy2(download_full_path, queue_full_path)

        print(f"[FileMover] - Moving: Video -> {queue_full_path} was added to the queue.", end='\n') if is_coppied else print('\nMoving: Failed to move to queue! See error above.')


    @staticmethod
    def __rename_file__(from_path, to_path):
        from_path = Path(from_path)
        to_path = Path(to_path)
        try:
            if not os.path.exists(to_path):
                os.rename(from_path, to_path)
                print(f"[FileMover] - Renaming File: {from_path} renamed to {to_path}.", end='\n')
            else:
                print(f"[FileMover] - Renaming File: {to_path} already exists.", end='\n')
                
                
            if os.path.exists(from_path):
                os.remove(from_path)
                print(f"[FileMover] - Renaming File: {from_path} removed.", end='\n')
                
        except PermissionError as pe:
            print(f'[ERROR][FileMover] - {repr(pe)}')
        except (FileExistsError, FileNotFoundError) as fe:
            print(f'[ERROR][FileMover] - {repr(fe)}')
        except Exception as e:
            print(f'[ERROR][FileMover] - {repr(e)}')
        
        
    @staticmethod
    def copy2(from_path, to_path):
        try:
            shutil.copy2(from_path, to_path)
            return True
        except Exception as ex:
            print(f'[ERROR][FileMover] - {repr(ex)}')
            return False
            
            
    @staticmethod
    def filename_sanitizer(filename):
        print(f'[FileMover] - File before sanitazing {filename}', end='\n')
        disalowed_characters = ApplicationVariables().get("DISALOWED_CHARACTERS")
        new_filename = filename
        
        for char in disalowed_characters:
            new_filename = new_filename.replace(char, '')
        
        print(f'[FileMover] - File after sanitazing {new_filename}', end='\n')
        return new_filename