from pathlib import Path
from typing import List
from rich.console import Console
from app.converters.audio.PydubConverter import PydubConverter
from app.extractors.audio.AudioExtractor import AudioExtractor
from app.helpers.utils.DirectoryUtils import DirectoryUtils
from app.helpers.utils.QueueUtil import QueueUtil
from app.helpers.utils.ValidatorUtil import ValidatorUtil
from app.providers import ProviderBase
from app.providers.ProviderFactory import ProviderFactory
from app.ui.menu import confirm_video_to_audio_extract, convertion_audio_menu, main_menu, provider_menu, read_urls
from app.config.LoggerConfig import logging

logger = logging.getLogger(__name__)


console = Console()


def main():
    console.print("Starting the main application...\n\n")
    
    while True:
        console.print()  # Print a newline for better readability
        MAIN_MENU_CHOICE = main_menu()
        
        if MAIN_MENU_CHOICE == "1":
            console.print("\n\nYou selected to start a new download.")
            logger.info("User selected to start a new download.")

            providers_menu_build()
        elif MAIN_MENU_CHOICE == "2":
            console.print("\n\nYou selected to view progress.")

            progress_menu_build()

        elif MAIN_MENU_CHOICE == "3":
            console.print("\n\nYou selected to convert video on queue to audio.")

            convertion_video_to_audio_menu_build()
        elif MAIN_MENU_CHOICE == "0":
            console.print("\n\nExiting the application...")

            break

        console.print()  # Print a newline for better readability

    console.print("Application has finished execution.")


def providers_menu_build():
    PROVIDER_CHOICE = provider_menu()

    if PROVIDER_CHOICE == "0":
        console.print("\n\nReturning to the previous menu.")

        return  

    URLS = read_urls()

    if not ValidatorUtil.is_url_valid(URLS):# not URLS:
        console.print("\nNo URLs were entered. Returning to the previous menu.")

        return

    provider: ProviderBase = None

    console.print(f"\nYou entered {len(URLS)} URLs to download.")
    logger.debug(f"User entered {len(URLS)} URLs to download.")

    if PROVIDER_CHOICE == "1":
        console.print("\n\nYou selected to download a Youtube video with yt-dlp.")

        provider = ProviderFactory.get_provider_instance('YTDLP')
    elif PROVIDER_CHOICE == "2":
        console.print("\n\nYou selected to download a Spotify audio with savify.")

        provider = ProviderFactory.get_provider_instance('SAVIFY')
    elif PROVIDER_CHOICE == "3":
        console.print("\n\nYou selected to download a PH video or image.")

        provider = ProviderFactory.get_provider_instance('PH')
            
    logger.debug(f"Starting download with provider: {provider.__class__.__name__}")
    provider.download(URLS)

    has_video_to_convert: bool = len(QueueUtil.get_queue_list()) > 0
    
    if has_video_to_convert:
        console.print("\nConfirm videos for audio extraction.")

        videos_to_confirm_convert: List[Path] = QueueUtil.get_queue_list().copy()

        for video in videos_to_confirm_convert:
            if confirm_video_to_audio_extract(video) in ("yes", "y"):
                QueueUtil.move_video_to_queue_folder(video)

            QueueUtil.remove_from_queue_list(video)


def progress_menu_build():
    ...


def convertion_video_to_audio_menu_build():
    videos = QueueUtil.get_video_in_audio_extract_queue()
    videos_to_extract: list[Path] = []
    CONVERT_CHOICE, VIDEO_PATH_CHOSEN = convertion_audio_menu(videos)

    if CONVERT_CHOICE == "0":
        console.print("\n\nReturning to the previous menu.")

        return
    elif CONVERT_CHOICE == "all":
        console.print("\n\nConverting all queued videos to audio.")

        for video in videos:
            videos_to_extract.append(video)
    else:
        console.print(f"\n\nConverting specific video to audio: {VIDEO_PATH_CHOSEN}")
        videos_to_extract.append(VIDEO_PATH_CHOSEN)

    audio_extractor = AudioExtractor(converter=PydubConverter())
    audio_extractor.extract_audio(videos_to_extract)


if __name__ == "__main__":
    DirectoryUtils.create_folders()
    main()