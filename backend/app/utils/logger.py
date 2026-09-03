"""
IntelliVault ~ Structured Logging Utility
Provides timestamped, multi-target logging for console and file retention.
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(name="intellivault", log_level=logging.INFO):
    """Configures and returns a structured logger instance."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(log_level)

    # Formatter: [ISO-8601 Timestamp] [Level] [Module:Line] - Message
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    try:
        log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, "intellivault.log")
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not initialize file log handler: {e}")

    return logger


# Global logger instance
logger = setup_logger()
