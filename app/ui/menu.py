from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def main_menu():
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold cyan]Python Stream Downloader[/bold cyan]\n\n"
            "1) New download\n"
            "2) View progress\n"
            "3) Convert video on queue to audio\n"
            "4) Organize music library\n"
            "\n"
            "0) Exit",
            title="Main Menu",
            padding=(1, 4)
        )
    )
    return Prompt.ask("Select option", choices=["1", "2", "3", "4", "0"])


def provider_menu():
    console.print(
        Panel.fit(
            "1) Download a Youtube video with yt-dlp\n"
            "2) Download a Spotify audio with savify\n"
            "3) Download a PH video or image\n"
            "\n"
            "0) Back to main menu",
            title="Select Provider",
            padding=(1, 4)
        )
    )
    return Prompt.ask("Provider", choices=["1", "2", "3", "0"])


def read_urls() -> list[str]:
    console.print("[bold]Enter URLs (one per line). Empty line to finish:[/bold]")
    urls = []
    while True:
        url = Prompt.ask("URL", default="", show_default=False)
        if not url:
            break
        urls.append(url)
    return urls


def convertion_audio_menu(videos):
    items = []
    items.append("[bold]Select video to convert:[/bold]\n")
    
    if not videos:
        console.print("\n")
        console.print(Panel.fit("No videos in the audio extraction queue.", title="Videos on Queue", padding=(1, 4)))
        return ("0", None)
    
    for idx, video in enumerate(videos, start=1):
        items.append(f"{idx}) {video.name}")

    items.append("\nall) convert all videos")
    items.append("0) Back to previous menu")
    console.print(Panel.fit("\n".join(items), title="Videos on Queue", padding=(1, 4)))

    choices = [str(i) for i in range(1, len(videos)+1)] + ["all", "0"]
    choice = Prompt.ask("Select video number or other option", choices=choices)

    video_path_chosen = videos[int(choice)-1] if choice.isdigit() and choice != "0" else None
    
    return (choice, video_path_chosen)


def confirm_video_to_audio_extract(file_path: Path) -> bool:
    console.print(
        Panel.fit(
            f"Do you want to queue '{file_path.name}' for audio extraction?",
            title="Queue video for audio extraction confirmation",
            padding=(1, 4)
        )
    )
    return Prompt.ask("Choose an option", choices=["yes", "y", "no", "n"])


def organize_menu():
    console.print(
        Panel.fit(
            "[bold cyan]Music Organizer[/bold cyan]\n\n"
            "1) Organize converted audio files\n"
            "2) Organize a custom folder\n"
            "\n"
            "0) Back to main menu",
            title="Organize Music",
            padding=(1, 4)
        )
    )
    return Prompt.ask("Select option", choices=["1", "2", "0"])


def organize_options_menu():
    console.print(
        Panel.fit(
            "1) Move files (relocate to organized folder)\n"
            "2) Copy files (keep originals)\n"
            "3) Dry run (preview only)\n"
            "\n"
            "0) Back",
            title="Organize Mode",
            padding=(1, 4)
        )
    )
    return Prompt.ask("Select mode", choices=["1", "2", "3", "0"])


def confirm_organize_after_conversion() -> bool:
    console.print(
        Panel.fit(
            "Do you want to organize the converted audio files now?\n"
            "(Sort them into Artist/Album/Title folders)",
            title="Organize converted files",
            padding=(1, 4)
        )
    )
    return Prompt.ask("Organize?", choices=["yes", "y", "no", "n"]) in ("yes", "y")
