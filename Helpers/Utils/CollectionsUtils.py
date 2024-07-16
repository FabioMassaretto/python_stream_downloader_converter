import os
from Helpers.Utils.ApplicationVariables import ApplicationVariables

queue_video_path = ApplicationVariables().get("QUEUE_VIDEO_PATH")
permitted_file_extension = ApplicationVariables().get("PERMITTED_FILE_EXTENSIONS")

permitted_video_files_dic = dict()


def populate_dict_permitted_video_files():
    permitted_video_files_dic.clear()
    files_in_queue_folder = os.listdir(queue_video_path)

    for file in files_in_queue_folder:
        extension_period_index = str(file).index(".")
        file_extension = file[extension_period_index:]

        if file_extension in permitted_file_extension and file not in permitted_video_files_dic:
            index = len(permitted_video_files_dic)
            new_item_dict = {index: file}
            permitted_video_files_dic.update(new_item_dict)

    return permitted_video_files_dic


def load_permitted_video_files_dic():
    permitted_video_files_dic = {}
    permitted_video_files_dic = populate_dict_permitted_video_files()
    total_permitted_video_files_dic = len(permitted_video_files_dic)

    return (permitted_video_files_dic, total_permitted_video_files_dic)
