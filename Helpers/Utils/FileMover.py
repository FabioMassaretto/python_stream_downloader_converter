import shutil
import os
from pathlib import Path

from Helpers.Utils.ApplicationVariables import ApplicationVariables


class FileMover:
    DOWNLOADED_VIDEO_PATH = ApplicationVariables().get("DEST_DOWNLOADED_VIDEO_PATH")
    QUEUE_VIDEO_PATH = ApplicationVariables().get("QUEUE_VIDEO_PATH")
    
    def move_to_queue_dir(self, file_path):
        full_path = Path(file_path)

        full_filename = full_path.name

        full_path_origin = self.DOWNLOADED_VIDEO_PATH + full_filename
        full_path_destination = self.QUEUE_VIDEO_PATH + full_filename

        is_copy = self.copy2(full_path_origin, full_path_destination)

        print(f"\nVideo: {full_filename} added to the queue.\n") if is_copy else print('\nFailed to copy! See error above.')

    def rename_file(self, from_path, to_path):
        is_renamed = self.copy2(from_path, to_path)

        print(f"\nFile: {from_path} was renamed to {to_path}.\n") if is_renamed else print('\nFailed to rename! See error above.')
        
    def copy2(self, from_path, to_path):
        try:
            shutil.copy2(from_path, to_path)
            return True
        except Exception as ex:
            print(f'Error: {repr(ex)}')
            return False
            
    def filename_sanitizer(self, filename):
        disalowed_characters = ApplicationVariables().get("DISALOWED_CHARACTERS")
        new_filename = ''
        
        for char in disalowed_characters:
            new_filename = filename.replace(char, '')
        
        return new_filename
        
        # if os.path.exists(self.DOWNLOADED_VIDEO_PATH):
        #     files_in_dir_list = os.listdir(self.DOWNLOADED_VIDEO_PATH)

        #     for file in files_in_dir_list:
        #         found_char = False
        #         for char in sanitazer_character:
        #             if char in file:
        #                 old_full_path = self.DOWNLOADED_VIDEO_PATH + file
        #                 new_filename = file.replace(char, '')
        #                 new_full_path = self.DOWNLOADED_VIDEO_PATH + new_filename
        #                 self.rename_file(old_full_path, new_full_path)

                    
        #             if found_char:
        #                 found_char = False
        #                 break