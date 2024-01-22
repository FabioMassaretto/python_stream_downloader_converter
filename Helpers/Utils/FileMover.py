import shutil

from Helpers.Utils.ApplicationVariables import ApplicationVariables

class FileMover:
    def move_to_queue_dir(file_path):
        filename_index = str(file_path).rindex('/')
        full_filename = file_path[filename_index+1:]

        full_src_path = ApplicationVariables["DEST_DOWNLOADED_VIDEO_PATH"].value + full_filename
        full_dest_path = ApplicationVariables["QUEUE_VIDEO_PATH"].value + full_filename

        try:
            shutil.copy2(full_src_path, full_dest_path)
            print(f"\nVideo: {full_filename} added to the queue.")
        except Exception as ex:
            print(ex)