import re
import shutil
from yt_dlp import YoutubeDL
from Helpers.Utils.ApplicationVariables import ApplicationVariables

__version__ = "1.0"
__author__ = "FabioMassa"

__dest_temp_ph_video_path__ = ApplicationVariables().get(
    "DEST_TEMP_PH_VIDEO_PATH")
__dest_downloaded_ph_video_path__ = ApplicationVariables().get(
    "DEST_DOWNLOADED_PH_VIDEO_PATH")


def main():
    url = input(" [?] Video URL: ")

    print(" [+] Downloading stand by\n")

    options = {
        'outtmpl': f'{__dest_temp_ph_video_path__}/%(id)s.%(ext)s',
    }

    # If anyone knows how to mute the output of this send help :,)
    ydl = YoutubeDL(options)
    with ydl:
        try:
            result = ydl.extract_info(
                url,
                download=True
            )

            temp_filename = result['id']

            filename = f'{result['uploader']
                          } - {result['title']} - {result['id']}'
            filename = re.sub('[^A-Za-z0-9 ]+', '', filename)
            filename = filename.replace(' ', '-')

            shutil.move(
                f"{__dest_temp_ph_video_path__}/{temp_filename}.mp4",
                f"{__dest_downloaded_ph_video_path__}/{filename}.mp4"
            )

        except Exception as e:
            print(result['title'])
            print(f'Exception: {repr(e)}')
            print('Failed to download the video!', end='\n\n')
