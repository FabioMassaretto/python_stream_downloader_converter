from rich.console import Console
from rich.panel import Panel
from app.ui.menu import main_menu


console = Console()

def build_ui():
    console.clear()
    console.print(
        Panel.fit(
            "[bold cyan]Python Stream Downloader[/bold cyan]\n\n"
            "Welcome to the Python Stream Downloader application!",
            title="Welcome",
        )
    )
    console.print("Please select an option from the main menu to get started.")
    console.print("You can download videos from various platforms and convert them to audio files.")
    console.print("Enjoy your experience!")

    main_menu()


def exit_ui():
    console.clear()
    console.print(
        Panel.fit(
            "[bold cyan]Thank you for using Python Stream Downloader![/bold cyan]\n\n"
            "Goodbye!",
            title="Exit",
        )
    )   
    console.print("We hope to see you again soon.")
