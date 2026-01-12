
from enum import Enum
from pathlib import Path


class ApplicationEnums(Enum):
    BASE_PATH = Path("./app")
    BASE_MEDIA_PATH = BASE_PATH / "media"
    QUEUE_BASE_PATH = BASE_MEDIA_PATH / "queue"
    QUEUE_VIDEO_PATH = QUEUE_BASE_PATH / "video"
    DEST_DOWNLOADED_VIDEO_PATH = BASE_MEDIA_PATH / "downloaded" / "video"
    DEST_CONVERTED_AUDIO_PATH = BASE_MEDIA_PATH / "converted" / "audio"
    DEST_DOWNLOADED_PH_VIDEO_PATH = BASE_MEDIA_PATH / "ph_downloaded" / "video"
    DEST_TEMP_PH_VIDEO_PATH = BASE_MEDIA_PATH / "ph_downloaded" / "temp" / "video"
    DEST_PICTURES_PATH = BASE_MEDIA_PATH / "ph_downloaded" / "pictures"
    ALLOWED_FILE_EXTENSIONS = ['.mp4', '.mkv', '.webm']
    DISALOWED_CHARACTERS =['＂', '"', '/', '\\']
