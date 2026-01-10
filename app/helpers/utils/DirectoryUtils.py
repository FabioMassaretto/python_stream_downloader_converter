import os

from app.helpers.utils.ApplicationVariables import ApplicationVariables
from app.config.LoggerConfig import logging

logger = logging.getLogger(__name__)

queue_video_path = ApplicationVariables.get("QUEUE_VIDEO_PATH")
dest_downloaded_video_path = ApplicationVariables.get("DEST_DOWNLOADED_VIDEO_PATH")
dest_converted_audio_path = ApplicationVariables.get("DEST_CONVERTED_AUDIO_PATH")
dest_temp_ph_video_path = ApplicationVariables.get("DEST_TEMP_PH_VIDEO_PATH")
dest_downloaded_ph_video_path = ApplicationVariables.get("DEST_DOWNLOADED_PH_VIDEO_PATH")
dest_pictures_path = ApplicationVariables.get("DEST_PICTURES_PATH")


class DirectoryUtils:
    def create_folders():
        if not os.path.exists(queue_video_path):
            logger.debug(f"Creating directory at: {queue_video_path}")

            os.makedirs(queue_video_path)

        if not os.path.exists(dest_downloaded_video_path):
            logger.debug(f"Creating directory at: {dest_downloaded_video_path}")

            os.makedirs(dest_downloaded_video_path)

        if not os.path.exists(dest_converted_audio_path):
            logger.debug(f"Creating directory at: {dest_converted_audio_path}")

            os.makedirs(dest_converted_audio_path)

        if not os.path.exists(dest_temp_ph_video_path):
            logger.debug(f"Creating directory at: {dest_temp_ph_video_path}")

            os.makedirs(dest_temp_ph_video_path)

        if not os.path.exists(dest_downloaded_ph_video_path):
            logger.debug(f"Creating directory at: {dest_downloaded_ph_video_path}")

            os.makedirs(dest_downloaded_ph_video_path)

        if not os.path.exists(dest_pictures_path):
            logger.debug(f"Creating directory at: {dest_pictures_path}")

            os.makedirs(dest_pictures_path)

        logger.debug("All necessary directories were created.")
