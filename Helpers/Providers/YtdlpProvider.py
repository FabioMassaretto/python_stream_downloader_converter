from yt_dlp import YoutubeDL, DownloadError
from Helpers.Utils import InputUtils
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.FileMover import FileMover


class YtdlpProvider:
    file_mover = FileMover()
    __dest_downloaded_video_path__ = ApplicationVariables().get("DEST_DOWNLOADED_VIDEO_PATH")
    video_filename = ''

    def __init__(self):
        print(" Chose => Download Youtube video \n")
        link = InputUtils.handle_user_url_input('youtube')

        if InputUtils.is_digit_and_go_back(link):
            return

        self.download(link)
        

    def my_hook(self, d):
        if d['status'] == 'finished':
            print('Done downloading, now converting ...')
            self.video_filename = f'{d['info_dict']['title']}.{d['info_dict']['ext']}'

    
    def download(self, link):
        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [self.my_hook],
            'paths': {'home': self.__dest_downloaded_video_path__ },
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'allow_multiple_audio_streams': True,
        }
        try:
            # Having issues with video title when has double quotes in it,
            # so the workaround was first replace with empty string, altering
            # the outtpml in ydl_opts
            with YoutubeDL() as ytdlp:
                info = ytdlp.extract_info(link)
                
                title: str = info['title']
                
                disalowed_characters = ApplicationVariables().get("DISALOWED_CHARACTERS")
                
                found_character = [1 for char in disalowed_characters if title.count(char) > 0]
                
                if len(found_character) > 0:
                    title_sanitazed = self.file_mover.filename_sanitizer(title)
                    
                    ydl_opts.update({'outtmpl': f'{title_sanitazed}.%(ext)s'})
                
            with YoutubeDL(ydl_opts) as ytdlp:
                
                ytdlp.download(link)
                downloaded_folder_path = ytdlp.get_output_path()
                full_video_path = downloaded_folder_path + self.video_filename
                new_full_video_path = self.file_mover.filename_sanitizer(full_video_path)
                
            self.move_for_audio_extraction(new_full_video_path)
                
        except DownloadError  as e:
            print(f"Error downloading {link}: {str(e)}", end='\n')
            
    def move_for_audio_extraction(self, full_video_path):
        convert_answer = input("Do you want to queue this video for audio extraction? (yes(y) or no(n)): ")
            
        while convert_answer not in ("yes", "y", "no", "n"):
            convert_answer = input(
                "Invalid answer. Do you want to queue this video for audio extraction? yes(y) or no(n): ")
        else:
            if convert_answer in ("no", "n"):
                return
            
            self.file_mover.move_to_queue_dir(full_video_path)
