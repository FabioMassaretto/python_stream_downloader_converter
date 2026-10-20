import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler

LOG_FILE = './app/logs/app.log'
BACKUP_COUNT = 1  # Keep 1 day of backups
WHEN = 'D'        # Rotate daily
INTERVAL = 1      # Rotate every 1 day

Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

console = Console()

rich_handler = RichHandler(
    console=console,
    rich_tracebacks=True,
    show_time=True,
    show_level=True,
    show_path=False,
    markup=False,
)
rich_handler.setLevel(logging.DEBUG)

file_handler = TimedRotatingFileHandler(
    filename=LOG_FILE,
    when=WHEN,
    interval=INTERVAL,
    backupCount=BACKUP_COUNT,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
# Replace existing handlers to avoid duplicates
root_logger.handlers = [rich_handler, file_handler]
