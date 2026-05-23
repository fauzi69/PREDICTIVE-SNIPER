import logging
import logging.handlers
import os
from core.config import Config


def setup_logger(name: str = "sniper") -> logging.Logger:
    """Setup comprehensive logging with file and console output."""

    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(Config.LOG_FILE) or "logs", exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_SIZE * 1024 * 1024,
        backupCount=Config.LOG_BACKUP_COUNT,
    )
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Global logger instance
logger = setup_logger()
