import shutil
import youtube_dl
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

    # If anyone knows how to mute the output of this send help :,)
    ydl = youtube_dl.YoutubeDL(
        {'outtmpl': f'{__dest_temp_ph_video_path__}/%(uploader)s - %(title)s - %(id)s.%(ext)s'})
    with ydl:
        try:
            result = ydl.extract_info(
                url,
                download=True
            )

            shutil.move(
                f"{__dest_temp_ph_video_path__}/{
                    result['uploader']} - {result['title']} - {result['id']}.mp4",
                f"{__dest_downloaded_ph_video_path__}/{
                    result['uploader']} - {result['title']} - {result['id']}.mp4"
            )

        except Exception:
            print('Failed to download the video!', end='\n\n')
