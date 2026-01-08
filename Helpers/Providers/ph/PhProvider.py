from Helpers.Providers.ph.modules import pictureDownloader, videoDownloader
from Helpers.Utils import TitleBuilder
from Helpers.Utils.ApplicationVariables import ApplicationVariables
from config.LoggerConfig import logging

logger = logging.getLogger(__name__)


class PhProvider:
    __dest_temp_ph_video_path__ = ApplicationVariables().get(
        "DEST_TEMP_PH_VIDEO_PATH")
    __dest_downloaded_ph_video_path__ = ApplicationVariables().get(
        "DEST_DOWNLOADED_PH_VIDEO_PATH")

    def __init__(self):
        menu_options = {
            "1":  {"function": videoDownloader.main, "name": "Download Video"},
            "2":  {"function": pictureDownloader.main, "name": "Download album or picture"},
            "0":  {"name": "Exit"}
        }

        while True:
            TitleBuilder.build_sub_title('PH Video and Image Downloader')
            indx = 0
            for key, val in menu_options.items():
                num = f"[{key}]"
                print(
                    f" {num:<6} {val['name']:<{35 if int(key) < 10 else 34}}",
                    end="" if indx % 2 == 0 else "\n"
                )
                indx += 1

            if indx % 2 == 1:
                print("")

            TitleBuilder.build_ending_sub_title()

            option = input("\n>>> ")

            if (option == '0'):
                break

            try:
                menu_options[option]["function"]()
            except KeyError:
                logger.error('Invalid Option!')
