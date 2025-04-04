from pytube import YouTube
from Helpers.Utils import InputUtils
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.FileMover import FileMover

from pytube.exceptions import AgeRestrictedError


class YoutubeProvider:
    __dest_downloaded_video_path__ = ApplicationVariables().get(
        "DEST_DOWNLOADED_VIDEO_PATH")

    def __init__(self):
        print(" Selected => Download Youtube video \n")
        link = InputUtils.handle_user_url_input('youtube')

        if InputUtils.is_digit_and_go_back(link):
            return

        self.download(link)

    def download(self, link):
        try:
            youtubeObject = YouTube(link, on_progress_callback=self.__progress_func__,
                                    on_complete_callback=self.__complete_func__)
            resolutions = youtubeObject.streams.all()

            resolutions_list: list = []
            for resolution in resolutions:
                print(resolution)
                resolutions_list.append(resolution.itag)

            while True:
                selected_resolution = input(
                    f'Select the resolution by itag number ({InputUtils.EXIT_NUMBER} to exit): ')

                if (selected_resolution == '0'):
                    break

                if (int(selected_resolution) in resolutions_list):
                    break

                print(f'Itag number {selected_resolution} not found. Choose another one.')

            youtubeObject.streams.order_by('resolution').desc().first().download(
                output_path=self.__dest_downloaded_video_path__)
        except AgeRestrictedError as ageErr:
            print(f"\nError: {ageErr}")
        except Exception as e:
            print("An error has occurred", end='\n')
            print(f"Error: {e}", end='\n')
            print(f"{repr(e)}", end='\n')

    def __progress_func__(self, stream, data_chunck, bytes_remaining):
        mb_unit_convert = 0.000001
        remaining_value_in_mb = round(bytes_remaining * mb_unit_convert, 2)

        print(f"Remaining: {remaining_value_in_mb} MB")

    def __complete_func__(self, stream, file_path):
        print(f"\nDownload is completed successfully and moved to {
              self.__dest_downloaded_video_path__}", end="\n\n")

        convert_answer = input(
            "Do you want to queue this video for convertion? (yes(y) or no(n)): ")
        while convert_answer not in ("yes", "y", "no", "n"):
            convert_answer = input(
                "Invalid answer. Do you want to queue this video for convertion? yes(y) or no(n): ")
        else:
            if convert_answer in ("no", "n"):
                return

            FileMover.move_to_queue_dir(file_path)
