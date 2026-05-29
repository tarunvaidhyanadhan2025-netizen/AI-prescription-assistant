"""
Logger Utility
Centralised logging configuration for the application.
Provides structured, levelled logging with optional file output.
"""

import logging
import os
import sys
from functools import lru_cache
from logging.handlers import RotatingFileHandler
from typing import Optional

from app.config import settings


class ColorFormatter(logging.Formatter):
    """
    Coloured console log formatter for development environments.
    Falls back to plain text in production.
    """

    COLOURS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        colour = self.COLOURS.get(record.levelname, self.RESET)
        record.levelname = f"{colour}{record.levelname:<8}{self.RESET}"
        return super().format(record)


def _build_handlers() -> list:
    """Build logging handlers based on configuration."""
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.ENVIRONMENT == "development":
        formatter = ColorFormatter(fmt=settings.LOG_FORMAT)
    else:
        formatter = logging.Formatter(fmt=settings.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # File handler (optional)
    if settings.LOG_FILE:
        log_dir = os.path.dirname(settings.LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=settings.LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(fmt=settings.LOG_FORMAT))
        handlers.append(file_handler)

    return handlers


def configure_root_logger():
    """
    Configure the root logger for the application.
    Should be called once at startup.
    """
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    for handler in _build_handlers():
        root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pytesseract").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


@lru_cache(maxsize=256)
def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.
    Uses lru_cache to avoid repeated logger creation.

    Usage:
        logger = get_logger(__name__)
        logger.info("Hello from module X")
    """
    logger = logging.getLogger(name)
    if not logger.handlers and not logger.propagate:
        # Ensure propagation so root handler is used
        logger.propagate = True
    return logger


# Configure root logger on module import
configure_root_logger()
