"""
Centralized logging configuration for the AI Employee system.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_dir=None):
    """
    Set up centralized logging configuration.

    Args:
        log_level: Logging level (default: INFO)
        log_dir: Directory for log files (default: ./logs in vault)
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Configure weekly_audit module logger
    weekly_audit_logger = logging.getLogger("weekly_audit")
    weekly_audit_logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler - if log directory is specified
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        log_file = log_path / "ai_employee.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Also add to vault logs if vault path is available
    vault_log_dir = Path("AI_Employee_Vault/Logs")
    if vault_log_dir.exists():
        vault_log_file = vault_log_dir / f"ai_employee_{Path.cwd().name}.log"
        vault_handler = logging.handlers.RotatingFileHandler(
            vault_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        vault_handler.setLevel(log_level)
        vault_handler.setFormatter(formatter)
        logger.addHandler(vault_handler)

    return logger


def get_logger(name):
    """
    Get a logger instance with the specified name.

    Args:
        name: Name of the logger

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize logging when module is imported
if __name__ != "__main__":
    setup_logging()