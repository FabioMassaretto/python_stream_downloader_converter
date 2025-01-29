from yt_dlp import YoutubeDL, DownloadError
from Helpers.Utils import InputUtils
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.FileMover import FileMover


class YtdlpProvider:
    file_mover = FileMover()
    __dest_downloaded_video_path__ = ApplicationVariables().get("DEST_DOWNLOADED_VIDEO_PATH")

    def __init__(self):
        print(" Chose => Download Youtube video \n")
        link = InputUtils.handle_user_url_input('youtube')

        if InputUtils.is_digit_and_go_back(link):
            return

        self.download(link)
        

    def my_hook(d):
        if d['status'] == 'finished':
            print('\nDone downloading, now converting ...', end='\n')
            
            video_ext = d['info_dict']['ext']
            video_title = d['info_dict']['title']
            temp_full_filename = d['filename']
            new_filename = f'{video_title}.{video_ext}'
            YtdlpProvider.process_finished_download(temp_full_filename, new_filename)


    @staticmethod
    def process_finished_download(temp_filename, new_filename):
        # Having issues with video title when has double quotes in it,
        # so the workaround was first replace with empty string, altering
        # the outtpml in ydl_opts
        new_video_filename = FileMover.filename_sanitizer(new_filename)
        
        FileMover.rename_downloaded_file(temp_filename, new_video_filename)
            
        YtdlpProvider.queue_for_audio_extraction(new_video_filename)
    
    
    ydl_opts = {
        # 'logger': YtDlpLogger(),
        'outtmpl': '%(id)s.%(ext)s',
        'progress_hooks': [my_hook],
        'paths': {'home': __dest_downloaded_video_path__ },
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]',
        # 'allow_multiple_audio_streams': True,
    }
    
    def download(self, link, opt=ydl_opts):
        try:               
            with YoutubeDL(opt) as ytdlp:
                ytdlp.download(link)
                
                # info = ytdlp.extract_info(link, download=False)
        except DownloadError as de:
            print(f'Error downloading {link}: {str(de)}', end='\n')
        except Exception as e:
            print(f'Error: {repr(e)}', end='\n')
            
    @staticmethod
    def queue_for_audio_extraction(filename):
        convert_answer = input(f"Do you want to queue '{filename}' for audio extraction? (yes(y) or no(n)): ")
            
        while convert_answer not in ("yes", "y", "no", "n"):
            convert_answer = input(
                f"Invalid answer. Do you want to queue '{filename}' for audio extraction? yes(y) or no(n): ")
        else:
            if convert_answer in ("no", "n"):
                return

            FileMover.move_to_queue_dir(filename)


class YtDlpLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            print(msg)
        else:
            self.info(msg)

    def info(self, msg):
        print(msg)

    def warning(self, msg):
        print(msg)

    def error(self, msg):
        print(msg)