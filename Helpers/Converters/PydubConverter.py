import os
from pydub import AudioSegment

from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.CollectionsUtils import load_permitted_video_files_dic
from Helpers.Utils.InputUtils import validate_return_user_input_choose
from Helpers.Utils.MenuUtils import mount_menu_for_videos_to_convert
from config.LoggerConfig import logging

logger = logging.getLogger(__name__)


class PydubConverter:
    dest_converted_audio_path = ApplicationVariables().get("DEST_CONVERTED_AUDIO_PATH")
    queue_video_path = ApplicationVariables().get("QUEUE_VIDEO_PATH")

    quantity_converted = 0

    def __init__(self):
        logger.info("Selected => Convert a Youtube video to audio file")

        files_to_convert, total_files = load_permitted_video_files_dic()

        try:
            mount_menu_for_videos_to_convert(files_to_convert, total_files)
            option_selected = validate_return_user_input_choose(total_files)
            self.process_convert_to_audio(option_selected, files_to_convert)

        except IndexError as ierr:
            logger.warning(ierr)
            return

    def process_convert_to_audio(self, user_option, video_files_dic):
        self.quantity_converted = 0
        is_converted_success = True

        if user_option == "all".lower():
            logger.info("Converting all file: ")

            for index in video_files_dic:
                is_converted_success = self.__convert_to_audio__(
                    self.queue_video_path, self.dest_converted_audio_path, video_files_dic, index) # TODO: remove duplicatesremove duplicates

        elif user_option == "back".lower():
            return
        elif user_option.isdigit():
            index = int(user_option)

            logger.info(f"Converting option: {index} and file: ")

            is_converted_success = self.__convert_to_audio__(
                self.queue_video_path, self.dest_converted_audio_path, video_files_dic, index) # TODO: remove duplicatesremove duplicates
        else:
            logger.error("Not a valid option!")

            return

        title_message = f"{'SUCCESS!' if is_converted_success else 'FAILED!'}"
        body_message = f"It was converted {
            self.quantity_converted} of total of {len(video_files_dic)} file"
        ending_message = f"{'s' if self.quantity_converted > 1 else ''}."

        logger.info(f"{title_message}{body_message}{ending_message}")

    def __convert_to_audio__(self, from_file_path, dest_path, video_files_dic, index, format_type="mp3"):
        file = video_files_dic.get(index)

        extension_dot = str(file).rfind('.')
        new_filename_without_extension = str(file).removesuffix(str(file)[extension_dot:])

        full_dest_file_path = dest_path + new_filename_without_extension
        full_from_file_path = from_file_path + file

        logger.info(f"Converting: {file}...")

        try:
            AudioSegment.from_file(full_from_file_path).export(full_dest_file_path + "." + format_type, format=format_type) # TODO: for yt-dlp provider there is an list out range error because of not getting the audio stream only video, the problem is inside pydub lib
            os.remove(full_from_file_path)
            self.quantity_converted += 1

            return True
        except FileNotFoundError:
            logger.error("The file was not found")

            return False
        except Exception as e:
            logger.error(f"{repr(e)}")

            return False
