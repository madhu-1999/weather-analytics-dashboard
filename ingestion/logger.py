import logging
from logging.handlers import RotatingFileHandler
import os

from dotenv import load_dotenv

load_dotenv()

LOG_DIR = os.getenv("LOG_DIR", "")
# Create custom logger
logger = logging.getLogger("ingestion")
logger.setLevel(logging.DEBUG)

# Create handlers and formatter
c_handler = logging.StreamHandler()
# max 5 mb file
f_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "ingestion.log"), maxBytes=5242880, encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s\n")
c_handler.setFormatter(formatter)
f_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(c_handler)
logger.addHandler(f_handler)
