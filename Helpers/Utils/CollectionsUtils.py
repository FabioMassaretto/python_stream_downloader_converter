import os
from Helpers.Utils.ApplicationVariables import ApplicationVariables


class CollectionsUtils:
    queue_video_path = ApplicationVariables().get("QUEUE_VIDEO_PATH")
    permitted_file_extension = ApplicationVariables().get("PERMITTED_FILE_EXTENSIONS")

    permitted_video_files_dic = dict()
    
    def populate_dict_permitted_video_files(self):
        self.permitted_video_files_dic.clear()
        files_in_queue_folder = os.listdir(self.queue_video_path)

        for file in files_in_queue_folder:
            extension_period_index = str(file).index(".")
            file_extension = file[extension_period_index:]

            if file_extension in self.permitted_file_extension and file not in self.permitted_video_files_dic:
                index = len(self.permitted_video_files_dic)
                new_item_dict = {index: file}
                self.permitted_video_files_dic.update(new_item_dict)
        
        return self.permitted_video_files_dic