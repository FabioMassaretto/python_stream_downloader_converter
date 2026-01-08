from Helpers.ConverterFactory import ConverterFactory
from Helpers.DownloaderFactory import DownloaderFactory
from Helpers.Utils import TitleBuilder
from Helpers.Utils.DirectoryUtils import DirectoryUtils
from config.LoggerConfig import logging

logger = logging.getLogger(__name__)


def menu_select(main_menu_option):
    downloader_factory = DownloaderFactory()
    converter_factory = ConverterFactory()

    option_id = menu_options.get(main_menu_option)[0]

    match option_id:
        case 'yt_dlp':
            downloader_factory.create('YTDLP')
        
        case 'pytube':
            downloader_factory.create('YOUTUBE')

        case 'pytube3':
            downloader_factory.create('PYTUBE3')

        case 'pytubefix':
            downloader_factory.create('PYTUBEFIX')

        case 'phube':
            downloader_factory.create('PHUBE')

        case 'savify':
            downloader_factory.create('SAVIFY')

        case 'convert':
            converter_factory.create('PYDUB')


menu_options: dict = {
    1: ["yt_dlp", "Download a Youtube video with (yt_dlp)"],
    2: ["pytube", "Download a Youtube video with (pytube) !deprecated¡"],
    3: ["pytube3", "Download a Youtube video with (pytube3) !deprecated¡"],
    4: ["pytubefix", "Download a Youtube video with (pytubefix)"],
    5: ["phube", "Download a PH video or image (PH)"],
    6: ["savify", "Download a Spotify audio (savify) - (Experimental)"],
    7: ["convert", "Convert video to audio file"],
    0: ["exit", "Exit"],
}


def display_menu():
    TitleBuilder.build_sub_title('MAIN MENU')
    for key, value in menu_options.items():
        print(f'( {key} ) - {value[1]} ')
    TitleBuilder.build_ending_sub_title()


def menu():
    while True:
        display_menu()
        option_selected = input("Enter the option number: ")
        print()

        if not option_selected.isdigit():
            while not option_selected.isdigit():
                option_selected = input("Enter a valid option number: ")

        option_selected = int(option_selected)

        if option_selected <= 0:
            break

        menu_select(option_selected)

    logger.info("Program exited.")
    return


if __name__ == "__main__":
    DirectoryUtils.create_folders()
    TitleBuilder.build_main_title('VIDEO DOWNLOADER AND CONVERTER')
    menu()
