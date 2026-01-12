import os
from pathlib import Path

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
        if not queue_video_path.exists():
            logger.debug(f"Creating directory at: {queue_video_path}")

            queue_video_path.mkdir(parents=True)

        if not dest_downloaded_video_path.exists():
            logger.debug(f"Creating directory at: {dest_downloaded_video_path}")

            dest_downloaded_video_path.mkdir(parents=True)

        if not dest_converted_audio_path.exists():
            logger.debug(f"Creating directory at: {dest_converted_audio_path}")

            dest_converted_audio_path.mkdir(parents=True)

        if not dest_temp_ph_video_path.exists():
            logger.debug(f"Creating directory at: {dest_temp_ph_video_path}")

            dest_temp_ph_video_path.mkdir(parents=True)

        if not dest_downloaded_ph_video_path.exists():
            logger.debug(f"Creating directory at: {dest_downloaded_ph_video_path}")

            dest_downloaded_ph_video_path.mkdir(parents=True)

        if not dest_pictures_path.exists():
            logger.debug(f"Creating directory at: {dest_pictures_path}")

            dest_pictures_path.mkdir(parents=True)

        logger.debug("All necessary directories were created.")
