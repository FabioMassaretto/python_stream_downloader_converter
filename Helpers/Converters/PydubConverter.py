import os
from pydub import AudioSegment

from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.CollectionsUtils import load_permitted_video_files_dic
from Helpers.Utils.InputUtils import validate_return_user_input_choose
from Helpers.Utils.MenuUtils import mount_menu_for_videos_to_convert


class PydubConverter:
    dest_converted_audio_path = ApplicationVariables().get("DEST_CONVERTED_AUDIO_PATH")
    queue_video_path = ApplicationVariables().get("QUEUE_VIDEO_PATH")

    quantity_converted = 0

    def __init__(self):
        print(" Selected => Convert a Youtube video to audio file \n")
        files_to_convert, total_files = load_permitted_video_files_dic()

        try:
            mount_menu_for_videos_to_convert(files_to_convert, total_files)
            option_selected = validate_return_user_input_choose(total_files)
            self.process_convert_to_audio(option_selected, files_to_convert)

        except IndexError as ierr:
            print(ierr)
            return

    def process_convert_to_audio(self, user_option, video_files_dic):
        self.quantity_converted = 0
        is_converted_success = True

        if user_option == "all".lower():
            print("Converting all file: ")

            for index in video_files_dic:
                is_converted_success = self.__convert_to_audio__(
                    self.queue_video_path, self.dest_converted_audio_path, video_files_dic, index)

        elif user_option == "back".lower():
            return
        elif user_option.isdigit():
            index = int(user_option)
            is_converted_success = self.__convert_to_audio__(
                self.queue_video_path, self.dest_converted_audio_path, video_files_dic, index)
        else:
            print("\nERROR: Not a valid option!")
            return

        title_message = f"\n{
            'SUCCESS!' if is_converted_success else 'FAILED!'} "
        body_message = f"It was converted {
            self.quantity_converted} of total of {len(video_files_dic)} file"
        ending_message = f"{'s' if self.quantity_converted > 1 else ''}."

        print(f"{title_message}{body_message}{ending_message}")

    def __convert_to_audio__(self, from_file_path, dest_path, video_files_dic, index, format_type="mp3"):
        file = video_files_dic.get(index)

        extension_dot = str(file).rfind('.')
        new_filename_without_extension = str(file).removesuffix(str(file)[extension_dot:])

        full_dest_file_path = dest_path + new_filename_without_extension
        full_from_file_path = from_file_path + file

        print(f"\n\nConverting: {file}...")

        try:
            AudioSegment.from_file(full_from_file_path).export(full_dest_file_path + "." + format_type, format=format_type) # TODO: for yt-dlp provider there is an list out range error because of not gtting the audio stream only video, the problem is inside pydub lib
            os.remove(full_from_file_path)
            self.quantity_converted += 1

            return True
        except FileNotFoundError:
            print("\nERROR: The file was not found")

            return False
        except Exception as e:
            print(f'ERROR: {repr(e)}')
            return False
