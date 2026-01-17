import logging
from logging.handlers import TimedRotatingFileHandler

LOG_FILE = './logs/app.log'
BACKUP_COUNT = 7  # Keep 7 days of backups
WHEN = 'D'        # Rotate daily
INTERVAL = 1      # Rotate every 1 day

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# handler = TimedRotatingFileHandler(
#     filename=LOG_FILE,
#     when=WHEN,
#     interval=INTERVAL,
#     backupCount=BACKUP_COUNT,
#     encoding='utf-8'
# )

# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)

# logging = logger

logging.basicConfig(    
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",            
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler(),
        TimedRotatingFileHandler(
            filename=LOG_FILE,
            when=WHEN,
            interval=INTERVAL,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
    ])