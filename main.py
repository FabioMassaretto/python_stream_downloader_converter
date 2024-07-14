from Helpers.ConverterFactory import ConverterFactory
from Helpers.DownloaderFactory import DownloaderFactory
from Helpers.Providers.Pytube3Provider import Pytube3Provider
from Helpers.Providers.ph.PhProvider import PhProvider
from Helpers.Providers.PytubefixProvider import PytubefixProvider
from Helpers.Providers.SavifyProvider import SavifyProvider
from Helpers.Providers.YoutubeProvider import YoutubeProvider
from Helpers.Utils import TitleBuilder
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.CollectionsUtils import CollectionsUtils
from Helpers.Utils.DirectoryUtils import DirectoryUtils

queue_video_path = ApplicationVariables().get("QUEUE_VIDEO_PATH")

collections_utils = CollectionsUtils()


def is_valid_option_chose(option_chose, dict_size):
    if (option_chose.isdigit() and int(option_chose) < dict_size) or option_chose in ('all', 'back'):
        return True

    return False


def validate_return_user_input_choose(dict_size):
    option_chose = input(
        "\nEnter the number corresponding to the file (or all or back): ")
    valid_option = is_valid_option_chose(option_chose, dict_size)

    while not valid_option:
        option_chose = input("Incorrect option, choose a valid option: ")

        if (is_valid_option_chose(option_chose, dict_size)):
            valid_option = True

    return option_chose


def load_permitted_video_files_dic():
    permitted_video_files_dic = {}
    permitted_video_files_dic = collections_utils.populate_dict_permitted_video_files()
    total_permitted_video_files_dic = len(permitted_video_files_dic)

    return (permitted_video_files_dic, total_permitted_video_files_dic)


def mount_menu_for_videos_to_convert(permitted_video_files_values, total):
    if total <= 0:
        raise IndexError(f"Directory {
                         queue_video_path} has no file to convert, put video file in it or download a video first.")

    print("all - To convert ALL files")
    print("back - Go back to main menu")
    for i in permitted_video_files_values:
        print(f"{i} - {permitted_video_files_values.get(i)}")


def menu_select(main_menu_option):
    downloader_factory = DownloaderFactory()
    converter_factory = ConverterFactory()

    option_id = menu_options.get(main_menu_option)[0]

    match option_id:
        case 'pytube':
            provider: YoutubeProvider = downloader_factory.create('YOUTUBE')

        case 'pytube3':
            provider: Pytube3Provider = downloader_factory.create('PYTUBE3')

        case 'pytubefix':
            provider: PytubefixProvider = downloader_factory.create(
                'PYTUBEFIX')

        case 'phube':
            provider: PhProvider = downloader_factory.create('PHUBE')

        case 'savify':
            provider: SavifyProvider = downloader_factory.create('SAVIFY')

        case 'convert':
            print(" Chose => Convert a Youtube video to audio file \n")
            files_to_convert, total_files = load_permitted_video_files_dic()
            pydub_converter = converter_factory.create('PYDUB')
            try:
                mount_menu_for_videos_to_convert(files_to_convert, total_files)
                option_chose = validate_return_user_input_choose(total_files)
                pydub_converter.process_convert_to_audio(
                    option_chose, files_to_convert)
            except IndexError as ierr:
                print(ierr)
                return


menu_options: dict = {
    1: ["pytube", "Download a Youtube video (pytube)"],
    2: ["pytube3", "Download a Youtube video (pytube3) !deprecated¡"],
    3: ["pytubefix", "Download a Youtube video (pytubefix)"],
    4: ["phube", "Download a PH video or image (PH)"],
    5: ["savify", "Download a Spotify audio (savify) - (Experimental)"],
    6: ["convert", "Convert video to audio file"],
    0: ["exit", "Exit"],
}


def display_menu():
    TitleBuilder.build_sub_title('MAIN MENU')
    for key, value in menu_options.items():
        print(f'( {key} ) - {value[1]} ')
    TitleBuilder.build_ending_sub_title()


def menu():
    while True:
        display_menu()
        option_chose = input("Enter the option number: ")
        print()

        if not option_chose.isdigit():
            while not option_chose.isdigit():
                option_chose = input("Enter a valid option number: ")

        option_chose = int(option_chose)

        if option_chose <= 0:
            break

        menu_select(option_chose)

    print("Program exited.")
    return


if __name__ == "__main__":
    TitleBuilder.build_main_title('VIDEO DOWNLOADER AND CONVERTER')
    DirectoryUtils.create_folders()
    menu()
