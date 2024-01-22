
import os
from pydub import AudioSegment
from Helpers.DownloaderFactory import DownloaderFactory
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.DirectoryUtils import DirectoryUtils

# TODO: To be removed after refactor
queue_video_path = ApplicationVariables["QUEUE_VIDEO_PATH"].value
dest_converted_audio_path = ApplicationVariables["DEST_CONVERTED_AUDIO_PATH"].value

refactor_permitted_files_dic = dict()
permitted_file_extension = ApplicationVariables["PERMITTED_FILE_EXTENSIONS"].value

def refactor_only_permitted_video_files():
    refactor_permitted_files_dic.clear()
    files_in_queue_folder = os.listdir(queue_video_path)

    for file in files_in_queue_folder:
        extension_period_index = str(file).index(".")
        file_extension = file[extension_period_index:]

        if file_extension in permitted_file_extension and file not in refactor_permitted_files_dic:
            index = len(refactor_permitted_files_dic)
            new_item_dict = {index: file}
            refactor_permitted_files_dic.update(new_item_dict)


def refactor_list_dir_files():
    refactor_only_permitted_video_files()

    if len(refactor_permitted_files_dic) <= 0:
        print(f"Directory {queue_video_path} with no file to convert, put video file in it or download a Youtube video first.")
        return -1
    
    print("all - To convert ALL files")
    print("back - Go back to main menu")
    for i in refactor_permitted_files_dic:
        print(f"{i} - {refactor_permitted_files_dic.get(i)}")


def process_convertion_audio():
    correct_option = False
    is_converted_success = False
    quantity_converted = 0

    if refactor_list_dir_files() == -1:
        return
    
    chose_option = input("\nEnter the number corresponding to the file (or all or back): ")

    if chose_option.isdigit():
        if int(chose_option) >= len(refactor_permitted_files_dic):
            while not correct_option:
                chose_option = input("Incorrect option, choose a valid option: ")

                if int(chose_option) < len(refactor_permitted_files_dic):
                    correct_option = True

    if chose_option == "all".lower():
        print("Converting all file: ")
        print(refactor_permitted_files_dic)

        for index in refactor_permitted_files_dic:
            is_converted_success = convert_to_audio_succesfully(queue_video_path, dest_converted_audio_path, index)
            quantity_converted += 1
    elif chose_option == "back".lower():
        return
    elif chose_option.isdigit():
        index = int(chose_option)
        is_converted_success = convert_to_audio_succesfully(queue_video_path, dest_converted_audio_path, index)
        quantity_converted += 1
    else:
        print("\nERROR: Not a valid option!")
        return
    
    if is_converted_success:
        print(f"\nSUCCESS! It was converted {quantity_converted} file{'s' if quantity_converted > 1 else ''}.")

    
def convert_to_audio_succesfully(from_file_path, dest_path, index, format_type="mp3"):
    file = refactor_permitted_files_dic.get(index)

    extension_period_index = str(file).index('.')
    new_filename_without_extension = file[:extension_period_index]

    full_dest_file_path = dest_path + new_filename_without_extension
    full_from_file_path = from_file_path + file
    
    print(f"Converting: {file}...")

    try:
        AudioSegment.from_file(full_from_file_path).export(full_dest_file_path, format=format_type)
        print(full_from_file_path)
        os.remove(full_from_file_path)

        return True        
    except FileNotFoundError:
        print("\nERROR: The file was not found")

        return False
    except:
        return False
        

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
    DirectoryUtils.create_folders()
    menu()