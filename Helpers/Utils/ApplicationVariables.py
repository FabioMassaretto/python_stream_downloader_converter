from enum import Enum


class ApplicationVariables(Enum):
    BASE_PATH="./"
    QUEUE_BASE_PATH=f"{BASE_PATH}queue/"
    QUEUE_VIDEO_PATH=f"{QUEUE_BASE_PATH}video/"
    DEST_DOWNLOADED_VIDEO_PATH=f"{BASE_PATH}downloaded/video/"
    DEST_CONVERTED_AUDIO_PATH=f"{BASE_PATH}converted/audio/"
