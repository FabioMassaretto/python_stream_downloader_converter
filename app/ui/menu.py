from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


def main_menu():
    console.clear()
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold cyan]Python Stream Downloader[/bold cyan]\n\n"
            "1) New download\n"
            "2) View progress\n"
            "3) Convert video on queue to audio\n"
            "\n"
            "0) Exit",
            title="Main Menu",
        )
    )
    return Prompt.ask("Select option", choices=["1", "2", "3", "0"])


def provider_menu():
    console.clear()
    console.print(
        Panel.fit(
            "1) Download a Youtube video with yt-dlp\n"
            "2) Download a Spotify audio with savify\n"
            "3) Download a PH video or image\n"
            "\n"
            "0) Back to main menu",
            title="Select Provider",
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
    console.clear()
    items = []
    items.append("[bold]Select video to convert:[/bold]\n")
    
    if not videos:
        console.print("\n")
        console.print(Panel.fit("No videos in the audio extraction queue.", title="Videos on Queue"))
        return ("0", None)
    
    for idx, video in enumerate(videos, start=1):
        items.append(f"{idx}) {video.name}")

    items.append("\nall) convert all videos")
    items.append("0) Back to previous menu")
    console.print(Panel.fit("\n".join(items), title="Videos on Queue"))

    choices = [str(i) for i in range(1, len(videos)+1)] + ["all", "0"]
    choice = Prompt.ask("Select video number or other option", choices=choices)

    video_path_chosen = videos[int(choice)-1] if choice.isdigit() and choice != "0" else None
    
    return (choice, video_path_chosen)


def is_video_to_audio_extract_queued(file_path: str) -> bool:
    console.print('\n\n                 ------------------ Queue for audio extraction --------------------------                 ')
    convert_answer = Prompt.ask(f"Do you want to queue '{file_path}' for audio extraction?", choices=["yes", "y", "no", "n"])

    if convert_answer in ("no", "n"):
        return False
    
    return True