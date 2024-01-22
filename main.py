from pytube import YouTube
from pydub import AudioSegment
import shutil
import os


base_path = "./"
queue_path = base_path + "queue/"
queue_video_path = queue_path + "video/"
destination_video_path = base_path + "downloaded/video/"
destination_converted_audio_path = base_path + "converted/audio/"
dir_permitted_files_list = list()
video_file_dict = {}
permitted_file_type = ('.mp4', '.mkv')


def progress_func(stream, data_chunck, bytes_remaining):
    mb_unit_convert = 0.000001
    remaining_value_in_mb = round(bytes_remaining * mb_unit_convert, 2)
 
    print(f"Remaining: {remaining_value_in_mb} MB")


def complete_func(stream, file_path):
    print(f"\nDownload is completed successfully and moved to {destination_video_path}", end="\n\n")

    convert_answer = input("Do you want to queue this video for convertion? (yes(y) or no(n)): ")
    while convert_answer not in ("yes", "y", "no", "n"):
        convert_answer = input("Invalid answer. Do you want to queue this video for convertion? yes(y) or no(n): ")
    else:
        if convert_answer in ("no", "n"):
            return
        
        move_to_queue_dir(file_path)
        

def download(link):
    youtubeObject = YouTube(link, on_progress_callback=progress_func, on_complete_callback=complete_func)
    youtubeObject = youtubeObject.streams.get_highest_resolution()

    try:
        youtubeObject.download(output_path=destination_video_path)
    except Exception as e:
        print("An error has occurred")
        print(e)


def move_to_queue_dir(file_path):
    filename_index = str(file_path).rindex('/')
    full_filename = file_path[filename_index+1:]

    full_src_path = destination_video_path + full_filename
    full_dest_path = queue_video_path + full_filename

    try:
        shutil.copy2(full_src_path, full_dest_path)
        print(f"\nVideo: {full_filename} added to the queue.")
    except Exception as ex:
        print(ex)

def only_permited_video_files():
    dir_files_list = os.listdir(queue_video_path)
    
    for file in dir_files_list:
        filename_index = str(file).index(".")
        format_type = file[filename_index:]

        if format_type in permitted_file_type:
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
            convert_to_audio(queue_video_path, destination_converted_audio_path, file)
            is_multi_file = True
    elif not chose_option.isdigit():
        print("\nERROR: Not a valid option!")
        return
    elif chose_option == "back".lower():
        return
    else:
        filename = video_file_dict.get(int(chose_option))
        print(f"Converting: {filename}...")
        convert_to_audio(queue_video_path, destination_converted_audio_path, filename)

    quantity_converted = str(len(video_file_dict)) if is_multi_file else "1"
    print(f"\nSUCCESS! It was converted {quantity_converted} file(s).")

def convert_to_audio(from_file_path, dest_path, filename, format_type="mp3"):
    format_type_index = str(filename).index('.')
    new_filename_without_type = filename[:format_type_index]

    full_dest_file_path = dest_path + new_filename_without_type
    full_from_file_path = from_file_path + filename

    try:
        AudioSegment.from_file(full_from_file_path).export(full_dest_file_path, format=format_type)
        os.remove(full_from_file_path)
    except FileNotFoundError:
        print("The file was not found")
        

def menu_select(main_menu_option):
    match main_menu_option:
        case 1:
            print(" Chose => Download a Youtube video \n")
            link = input("Enter the YouTube video URL: ")
            download(link)
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

def create_folders():
    if not os.path.exists(queue_video_path):
        os.makedirs(queue_video_path)
    
    if not os.path.exists(destination_video_path):
        os.makedirs(destination_video_path)
    
    if not os.path.exists(destination_converted_audio_path):
        os.makedirs(destination_converted_audio_path)


if __name__ == "__main__":
    print("\n\n------------------------- YOUTUBE DOWNLOADER AND CONVERTER -------------------------")
    create_folders()
    menu()