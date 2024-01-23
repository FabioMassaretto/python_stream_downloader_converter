import os

from Helpers.Utils.ApplicationVariables import ApplicationVariables

queue_video_path = ApplicationVariables().get("QUEUE_VIDEO_PATH")
dest_downloaded_video_path = ApplicationVariables().get("DEST_DOWNLOADED_VIDEO_PATH")
dest_converted_audio_path = ApplicationVariables().get("DEST_CONVERTED_AUDIO_PATH")

class DirectoryUtils:
    def create_folders():
        if not os.path.exists(queue_video_path):
            os.makedirs(queue_video_path)
        
        if not os.path.exists(dest_downloaded_video_path):
            os.makedirs(dest_downloaded_video_path)
        
        if not os.path.exists(dest_converted_audio_path):
            os.makedirs(dest_converted_audio_path)
