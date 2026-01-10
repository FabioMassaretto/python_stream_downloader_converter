from pathlib import Path
from pydub import AudioSegment
from app.config.LoggerConfig import logging
from app.converters.audio.AudioConverter import AudioConverter
from app.helpers.utils.FileMover import FileMover
from app.helpers.utils.ApplicationVariables import ApplicationVariables

logger = logging.getLogger(__name__)


class PydubConverter(AudioConverter):
    dest_converted_audio_path = ApplicationVariables.get("DEST_CONVERTED_AUDIO_PATH")
    queue_video_path = ApplicationVariables.get("QUEUE_VIDEO_PATH")

    quantity_converted = 0

    def __init__(self):
        logger.info("Selected => Convert a Youtube video to audio file")


    def process_to_extract_audio(self, videos_path: list[Path]):
        self.__convert_to_audio__(videos_path)


    def __convert_to_audio__(self, videos_path: list[Path], format_type: str = "mp3"):
        for video_path in videos_path:
            full_from_file_path = Path(self.queue_video_path) / video_path.name
            full_dest_file_path = Path(self.dest_converted_audio_path) / f"{video_path.stem}.{format_type}"

            logger.info(f"Converting: {video_path.name}...")

            try:
                AudioSegment.from_file(full_from_file_path).export(full_dest_file_path, format=format_type)
                FileMover.remove(video_path)
                self.quantity_converted += 1

            except FileNotFoundError as fnfe:
                logger.error(f"{repr(fnfe)}")

                continue
            except Exception as e:
                logger.error(f"{repr(e)}")

                continue


        body_message = f"It was converted {self.quantity_converted} of total of {len(videos_path)} file"
        ending_message = f"{'s' if self.quantity_converted > 1 else ''}."

        logger.info(f"{body_message}{ending_message}")
