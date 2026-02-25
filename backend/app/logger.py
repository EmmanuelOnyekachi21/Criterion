"""Centralized logging configuration for the application.

This module provides a configured logger instance with support for both
console and file logging with rotation, respecting environment-based
configuration.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from app.config import settings


def setup_logger(
    name: str = 'criterion',
    level: Optional[str] = None,
) -> logging.Logger:
    """Configure and return a logger instance.

    Creates a logger with console output and optional file logging with
    rotation. Prevents duplicate handlers if logger is already configured.

    Args:
        name (str): Logger name (typically app name or module name).
        level (Optional[str]): Log level override (uses settings.log_level
            if None).

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(name)

    log_level = level or settings.log_level
    logger.setLevel(getattr(logging, log_level))

    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt=settings.log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (STDOUT)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (with rotation) - optional
    if settings.log_to_file:
        # Ensure log directory exists
        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=settings.log_file_path,
            maxBytes=settings.log_file_max_bytes,
            backupCount=settings.log_file_backup_count,
            encoding="utf-8"
        )

        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logger()
