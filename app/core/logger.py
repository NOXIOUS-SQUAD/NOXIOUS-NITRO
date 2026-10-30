import logging
import os
from datetime import datetime

from app.config import LOG_DIR


def create_logger():
    os.makedirs(LOG_DIR, exist_ok=True)
    path = os.path.join(LOG_DIR, f"nitro_{datetime.now():%Y%m%d_%H%M%S}.log")
    logger = logging.getLogger("nitro")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(fh)
    return logger, path
