import logging
from logging.handlers import TimedRotatingFileHandler

LOG_FILE = './app/logs/app.log'
BACKUP_COUNT = 1  # Keep 7 days of backups
WHEN = 'D'        # Rotate daily
INTERVAL = 1      # Rotate every 1 day

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",            
    handlers=[
        logging.StreamHandler(),
        TimedRotatingFileHandler(
            filename=LOG_FILE,
            when=WHEN,
            interval=INTERVAL,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
    ])