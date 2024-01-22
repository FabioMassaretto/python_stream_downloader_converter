import os

from Helpers.Utils.ApplicationVariables import ApplicationVariables

queue_video_path = ApplicationVariables["QUEUE_VIDEO_PATH"].value
dest_downloaded_video_path = ApplicationVariables["DEST_DOWNLOADED_VIDEO_PATH"].value
dest_converted_audio_path = ApplicationVariables["DEST_CONVERTED_AUDIO_PATH"].value

class Directory:
    def create_folders():
        if not os.path.exists(queue_video_path):
            os.makedirs(queue_video_path)
        
        if not os.path.exists(dest_downloaded_video_path):
            os.makedirs(dest_downloaded_video_path)
        
        if not os.path.exists(dest_converted_audio_path):
            os.makedirs(dest_converted_audio_path)
