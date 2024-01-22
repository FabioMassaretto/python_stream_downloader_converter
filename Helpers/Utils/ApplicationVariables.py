from enum import Enum


class ApplicationVariables(Enum):
    BASE_PATH="./"
    BASE_MEDIA_PATH="media/"
    QUEUE_BASE_PATH=f"{BASE_MEDIA_PATH}queue/"
    QUEUE_VIDEO_PATH=f"{QUEUE_BASE_PATH}video/"
    DEST_DOWNLOADED_VIDEO_PATH=f"{BASE_MEDIA_PATH}downloaded/video/"
    DEST_CONVERTED_AUDIO_PATH=f"{BASE_MEDIA_PATH}converted/audio/"
    PERMITTED_FILE_EXTENSIONS=['.mp4', '.mkv']