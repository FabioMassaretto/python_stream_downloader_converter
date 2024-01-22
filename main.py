from Helpers.ConverterFactory import ConverterFactory
from Helpers.DownloaderFactory import DownloaderFactory
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.CollectionsUtils import CollectionsUtils
from Helpers.Utils.DirectoryUtils import DirectoryUtils

queue_video_path = ApplicationVariables["QUEUE_VIDEO_PATH"].value

collections_utils = CollectionsUtils()


def is_valid_option_chose(option_chose, dict_size):
    if (option_chose.isdigit() and int(option_chose) < dict_size) or option_chose in ('all', 'back'):
        return True
        
    return False


def validate_return_user_input_choose(dict_size):
    option_chose = input("\nEnter the number corresponding to the file (or all or back): ")
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
        raise IndexError(f"Directory {queue_video_path} has no file to convert, put video file in it or download a video first.")

    print("all - To convert ALL files")
    print("back - Go back to main menu")
    for i in permitted_video_files_values:
        print(f"{i} - {permitted_video_files_values.get(i)}")


def menu_select(main_menu_option):
    downloader_factory = DownloaderFactory()
    converter_factory = ConverterFactory()

    match main_menu_option:
        case 1:
            print(" Chose => Download a Youtube video \n")
            link = input("Enter the YouTube video URL: ")
            youtube_downloader = downloader_factory.create('YOUTUBE')
            youtube_downloader.download(link)
        case 2:
            print(" Chose => Convert a Youtube video to audio file \n")
            files_to_convert, total_files = load_permitted_video_files_dic()
            pydub_converter = converter_factory.create('PYDUB')
            try:
                mount_menu_for_videos_to_convert(files_to_convert, total_files)
                option_chose = validate_return_user_input_choose(total_files)
                pydub_converter.process_convert_to_audio(option_chose, files_to_convert)
            except IndexError as ierr:
                print(ierr)
                return


def display_menu():
    print("\n#################### MENU ####################")
    print("( 1 ) - Download a Youtube video")
    print("( 2 ) - Convert a Youtube video to audio file")
    print("( 0 ) - Exit")
    print("##############################################")


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
    
    print("Program finnished")
    return


if __name__ == "__main__":
    print("\n\n------------------------- YOUTUBE DOWNLOADER AND CONVERTER -------------------------")
    DirectoryUtils.create_folders()
    menu()