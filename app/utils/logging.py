"""
Logging configuration for the NesterVoiceAI application.

This module provides centralized logging setup using loguru.
"""

import os
import sys
from typing import Optional

from loguru import logger


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
) -> None:
    """Configure application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file for persistent logging
        rotation: Log rotation size/time (e.g., "10 MB", "1 day")
        retention: Log retention period (e.g., "7 days", "1 month")
    """
    # Remove default handler
    logger.remove()

    # Get log level from environment or use provided level
    log_level = os.getenv("LOG_LEVEL", level).upper()

    # Console handler with colored output
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        colorize=True,
    )

    # File handler if log file is specified
    if log_file:
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation=rotation,
            retention=retention,
            compression="gz",
        )

    logger.info(f"Logging configured with level: {log_level}")


def get_logger(name: str):
    """Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logger.bind(name=name)
