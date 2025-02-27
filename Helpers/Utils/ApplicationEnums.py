
from enum import Enum


class ApplicationEnums(Enum):
    BASE_PATH = "."
    BASE_MEDIA_PATH = f"{BASE_PATH}/media"
    QUEUE_BASE_PATH = f"{BASE_MEDIA_PATH}/queue"
    QUEUE_VIDEO_PATH = f"{QUEUE_BASE_PATH}/video/"
    DEST_DOWNLOADED_VIDEO_PATH = f"{BASE_MEDIA_PATH}/downloaded/video/"
    DEST_CONVERTED_AUDIO_PATH = f"{BASE_MEDIA_PATH}/converted/audio/"
    DEST_DOWNLOADED_PH_VIDEO_PATH = f"{BASE_MEDIA_PATH}/ph_downloaded/video"
    DEST_TEMP_PH_VIDEO_PATH = f"{BASE_MEDIA_PATH}/temp/video"
    DEST_PICTURES_PATH = f"{BASE_MEDIA_PATH}/pictures"
    PERMITTED_FILE_EXTENSIONS = ['.mp4', '.mkv', '.webm']
    DISALOWED_CHARACTERS =['＂', '"', '/', '\\']
