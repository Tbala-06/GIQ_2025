#!/usr/bin/env python3
"""
Logging utilities for robot controller.
Provides console and file logging with proper formatting.
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_file=None, log_level='INFO'):
    """
    Setup logging configuration for the entire application.

    Args:
        log_file (str): Path to log file. If None, logs only to console
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger: Root logger instance
    """
    # Convert string level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        try:
            # Create log directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Could not create file logger: {e}")

    root_logger.info("=" * 60)
    root_logger.info("Logging system initialized")
    root_logger.info(f"Log level: {log_level}")
    if log_file:
        root_logger.info(f"Log file: {log_file}")
    root_logger.info("=" * 60)

    return root_logger


def get_logger(name):
    """
    Get a logger for a specific module.

    Args:
        name (str): Logger name (typically __name__)

    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
