from pytube import YouTube
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.FileMover import FileMover


class YoutubeProvider:
    __dest_downloaded_video_path__ = ApplicationVariables["DEST_DOWNLOADED_VIDEO_PATH"].value
        
    def download(self, link):
        youtubeObject = YouTube(link, on_progress_callback=self.__progress_func__, on_complete_callback=self.__complete_func__)
        youtubeObject = youtubeObject.streams.get_highest_resolution()

        try:
            print("DEBUG")
            print(self.__dest_downloaded_video_path__)
            youtubeObject.download(output_path=self.__dest_downloaded_video_path__)
        except Exception as e:
            print("An error has occurred")
            print(e)

    def __progress_func__(self, stream, data_chunck, bytes_remaining):
        mb_unit_convert = 0.000001
        remaining_value_in_mb = round(bytes_remaining * mb_unit_convert, 2)
    
        print(f"Remaining: {remaining_value_in_mb} MB")


    def __complete_func__(self, stream, file_path):
        print(f"\nDownload is completed successfully and moved to {self.__dest_downloaded_video_path__}", end="\n\n")

        convert_answer = input("Do you want to queue this video for convertion? (yes(y) or no(n)): ")
        while convert_answer not in ("yes", "y", "no", "n"):
            convert_answer = input("Invalid answer. Do you want to queue this video for convertion? yes(y) or no(n): ")
        else:
            if convert_answer in ("no", "n"):
                return
            
            FileMover.move_to_queue_dir(file_path)