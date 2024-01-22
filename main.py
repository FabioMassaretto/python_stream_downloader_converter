
import os
from pydub import AudioSegment
from Helpers.DownloaderFactory import DownloaderFactory
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.Directory import Directory

# TODO: To be removed after refactor
queue_video_path = ApplicationVariables["QUEUE_VIDEO_PATH"].value
dest_converted_audio_path = ApplicationVariables["DEST_CONVERTED_AUDIO_PATH"].value

dir_permitted_files_list = list()
video_file_dict = {}
permitted_file_extension = ('.mp4', '.mkv')


def only_permited_video_files():
    dir_queue_files_list = os.listdir(queue_video_path)
    
    for file in dir_queue_files_list:
        extension_period_index = str(file).index(".")
        file_extension = file[extension_period_index:]

        if file_extension in permitted_file_extension:
            dir_permitted_files_list.append(file)


def list_dir_files():
    only_permited_video_files()

    if len(dir_permitted_files_list) <= 0:
        print(f"Directory {queue_video_path} with no file to convert, put video file in it or download a Youtube video first.")
        return -1
    
    print("all - To convert ALL files")
    print("back - Go back to main menu")
    for i, item in enumerate(dir_permitted_files_list):
        print(f"{i} - {item}")
        video_file_dict[i] = item


def process_convertion_audio():
    correct_option = False
    is_multi_file = False

    if list_dir_files() == -1:
        return
    
    chose_option = input("\nEnter the number corresponding to the file (or all or back): ")

    if chose_option.isdigit():
        if int(chose_option) >= len(video_file_dict):
            while not correct_option:
                chose_option = input("Incorrect option, choose a valid option: ")

                if int(chose_option) < len(video_file_dict):
                    correct_option = True

    if chose_option == "all".lower():
        print("Converting all file: ")

        for i in video_file_dict:
            file = video_file_dict.get(i)
            print(f"Converting: {file}...")
            convert_to_audio(queue_video_path, dest_converted_audio_path, file)
            is_multi_file = True
    elif not chose_option.isdigit():
        print("\nERROR: Not a valid option!")
        return
    elif chose_option == "back".lower():
        return
    else:
        filename = video_file_dict.get(int(chose_option))
        print(f"Converting: {filename}...")
        convert_to_audio(queue_video_path, dest_converted_audio_path, filename)

    quantity_converted = str(len(video_file_dict)) if is_multi_file else "1"
    print(f"\nSUCCESS! It was converted {quantity_converted} file(s).")

def convert_to_audio(from_file_path, dest_path, filename, format_type="mp3"):
    extension_period_index = str(filename).index('.')
    new_filename_without_extension = filename[:extension_period_index]

    full_dest_file_path = dest_path + new_filename_without_extension
    full_from_file_path = from_file_path + filename

    try:
        AudioSegment.from_file(full_from_file_path).export(full_dest_file_path, format=format_type)
        os.remove(full_from_file_path)
    except FileNotFoundError:
        print("The file was not found")
        

def menu_select(main_menu_option):
    downloader_factory = DownloaderFactory()

    match main_menu_option:
        case 1:
            print(" Chose => Download a Youtube video \n")
            link = input("Enter the YouTube video URL: ")
            downloader_factory.download('YOUTUBE', link)
        case 2:
            print(" Chose => Convert a Youtube video to audio file \n")
            process_convertion_audio()


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
    Directory.create_folders()
    menu()