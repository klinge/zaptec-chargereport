import logging
import os
from datetime import datetime


def setup_logger():
    # Get data directory from .env and create logs directory if it doesn't exist
    data_dir = os.getenv("DATA_DIR", "data/logs")
    log_dir = f"{data_dir}/logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure logger
    logger = logging.getLogger("zaptec-chargereport")

    # If logger already has handlers, assume it's configured and return
    if logger.hasHandlers():
        return logger

    # Get log level from .env, default to INFO if not set
    log_level = os.getenv("LOG_LEVEL", "INFO")
    # Convert string to logging level constant
    numeric_level = getattr(logging, log_level.upper())
    
    # Main logger always allows DEBUG messages
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Prevent log propagation

    # File handler captures DEBUG messages
    log_file = f"{log_dir}/charge_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Console handler uses logging level from .env
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)

    # Format for the logs
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
