import logging
import os
from datetime import datetime

def setup_logger():
    # Create logs directory if it doesn't exist
    os.makedirs('data/logs', exist_ok=True)
    
    # Configure logger
    logger = logging.getLogger('zaptec-chargereport')
    logger.setLevel(logging.INFO)
    
    # File handler with current date
    log_file = f"data/logs/charge_report_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Format for the logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
