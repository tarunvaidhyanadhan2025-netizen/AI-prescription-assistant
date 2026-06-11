import logging
import sys
from app.core.settings import settings


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        if settings.LOG_FILE:
            fh = logging.FileHandler(settings.LOG_FILE)
            fh.setFormatter(fmt)
            logger.addHandler(fh)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    return logger
