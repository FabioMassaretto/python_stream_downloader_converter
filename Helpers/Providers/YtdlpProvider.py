from yt_dlp import YoutubeDL, DownloadError
from Helpers.Utils import InputUtils
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from Helpers.Utils.FileMover import FileMover


class YtdlpProvider:
    file_mover = FileMover()
    __dest_downloaded_video_path__ = ApplicationVariables().get("DEST_DOWNLOADED_VIDEO_PATH")

    def __init__(self):
        print(" Selected => Download Youtube video \n")
        link = InputUtils.handle_user_url_input('youtube')

        if InputUtils.is_digit_and_go_back(link):
            return

        self.download(link)
    
    
    ydl_opts = {
        'outtmpl': '%(fulltitle)s.%(ext)s',
        'windowsfilenames': True,
        # 'progress_hooks': [my_hook],
        'paths': {'home': __dest_downloaded_video_path__ },
        'format': 'bestvideo[height=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
        # 'format': "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        # 'format': "(bv*[vcodec~='^((he|a)vc|h26[45])']+ba) / (bv*+ba/b)",
        # 'format': "bestvideo[height>=720]best[ext=mp4]",
    }
    
    def download(self, link, opt=ydl_opts):
            with YoutubeDL(opt) as ytdlp:
                try:               
                    ytdlp.download(link)
                    extract_info = ytdlp.extract_info(link, download=False)
                    video_filename = extract_info['fulltitle']
                    video_extension = extract_info['ext']
                    full_video_filename = f'{video_filename}.{video_extension}'
                except DownloadError as de:
                    print(f'Error downloading {link}: {str(de)}', end='\n')
                    return
                except Exception as e:
                    print(f'Error: {repr(e)}', end='\n')
                    return
                
                # info = ytdlp.extract_info(link, download=False)
            YtdlpProvider.queue_for_audio_extraction(full_video_filename)
          
            
    @staticmethod
    def queue_for_audio_extraction(filename):
        print(' ------------------ Queue for audio extraction --------------------------')
        convert_answer = input(f"Do you want to queue '{filename}' for audio extraction? (yes(y) or no(n)): ")
            
        while convert_answer not in ("yes", "y", "no", "n"):
            convert_answer = input(
                f"Invalid answer. Do you want to queue '{filename}' for audio extraction? yes(y) or no(n): ")
        else:
            if convert_answer in ("no", "n"):
                return

            FileMover.move_to_queue_dir(filename)
