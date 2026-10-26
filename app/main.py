from pathlib import Path
from typing import List
from rich.console import Console
from rich.prompt import Prompt
from app.converters.audio.PydubConverter import PydubConverter
from app.extractors.audio.AudioExtractor import AudioExtractor
from app.helpers.utils.DirectoryUtils import DirectoryUtils
from app.helpers.utils.QueueUtil import QueueUtil
from app.helpers.utils.ValidatorUtil import ValidatorUtil
from app.helpers.utils.MusicOrganizer import organize_converted_audio, organize_specific_files
from app.providers import ProviderBase
from app.providers.ProviderFactory import ProviderFactory
from app.ui.menu import (
    confirm_video_to_audio_extract,
    convertion_audio_menu,
    main_menu,
    provider_menu,
    read_urls,
    organize_menu,
    organize_options_menu,
    confirm_organize_after_conversion,
)
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
        elif MAIN_MENU_CHOICE == "4":
            console.print("\n\nYou selected to organize music library.")

            organize_menu_build()
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

    # After conversion, offer to organize the newly converted files
    if confirm_organize_after_conversion():
        from app.helpers.utils.ApplicationVariables import ApplicationVariables
        dest_audio = ApplicationVariables.get("DEST_CONVERTED_AUDIO_PATH")

        # Build list of the files that were just converted
        converted_files = []
        for v in videos_to_extract:
            mp3 = dest_audio / f"{v.stem}.mp3"
            if mp3.exists():
                converted_files.append(mp3)

        if converted_files:
            organize_specific_files(
                files=converted_files,
                mode="move",
                use_online=True,
            )
        else:
            # Fallback: organize the entire converted folder
            organize_converted_audio(mode="move", use_online=True)


def organize_menu_build():
    choice = organize_menu()

    if choice == "0":
        console.print("\n\nReturning to the previous menu.")
        return

    # Get mode
    mode_choice = organize_options_menu()
    if mode_choice == "0":
        return

    dry_run = mode_choice == "3"
    mode = "move" if mode_choice == "1" else "copy"

    if choice == "1":
        # Organize converted audio
        console.print("\n\nOrganizing converted audio files...")
        organize_converted_audio(mode=mode, use_online=True, dry_run=dry_run)

    elif choice == "2":
        # Organize custom folder
        folder = Prompt.ask("Enter folder path to organize")
        folder_path = Path(folder).resolve()

        if not folder_path.is_dir():
            console.print(f"[bold red]Error:[/bold red] {folder_path} is not a directory.")
            return

        output = Prompt.ask(
            "Output folder (leave empty for <input>/organized)",
            default="",
            show_default=False,
        )
        output_path = Path(output).resolve() if output else None

        from app.helpers.utils.MusicOrganizer import organize_directory
        organize_directory(
            input_dir=folder_path,
            output_dir=output_path,
            mode=mode,
            use_online=True,
            dry_run=dry_run,
            console=console,
        )


if __name__ == "__main__":
    DirectoryUtils.create_folders()
    main()
