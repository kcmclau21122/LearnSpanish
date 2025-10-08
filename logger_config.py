"""
Logger Configuration Module
===========================
This module handles all logging configuration for the Spanish Learning Assistant.
It sets up file and console logging with rotation, formatting, and log cleanup.

Functions:
    - setup_logging: Initialize logging system with file and console handlers
    - get_logger: Get a logger instance for a specific module
    - get_log_file_path: Get the path to the current log file
    - clear_old_logs: Remove log files older than specified days
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from typing import Optional


# Log directory setup
LOG_DIR = Path.home() / ".spanish_tutor" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Current log file
LOG_FILE = LOG_DIR / f"spanish_tutor_{datetime.now().strftime('%Y%m%d')}.log"

# Global flag to track if logging has been initialized
_logging_initialized = False


def setup_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> None:
    """
    Set up logging configuration for the application.
    
    Configures both file and console logging with rotation. File logs include
    detailed information, while console logs are more concise.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        max_bytes: Maximum size per log file before rotation
        backup_count: Number of backup log files to keep
        
    Example:
        >>> setup_logging(log_level="INFO", log_to_file=True)
    """
    global _logging_initialized
    
    if _logging_initialized:
        return
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    if log_to_file:
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not set up file logging: {e}", file=sys.stderr)
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('streamlit').setLevel(logging.WARNING)
    
    _logging_initialized = True
    
    # Log initialization
    root_logger.info("=" * 80)
    root_logger.info("Logging system initialized")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info(f"Log file: {LOG_FILE}")
    root_logger.info("=" * 80)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module (typically __name__)
        
    Returns:
        logging.Logger: Logger instance for the module
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    return logging.getLogger(name)


def get_log_file_path() -> str:
    """
    Get the path to the current log file.
    
    Returns:
        str: Absolute path to the log file
        
    Example:
        >>> path = get_log_file_path()
        >>> print(f"Logs are at: {path}")
    """
    return str(LOG_FILE.absolute())


def clear_old_logs(days: int = 30) -> int:
    """
    Remove log files older than specified number of days.
    
    Scans the log directory and removes files older than the given age.
    This helps manage disk space usage.
    
    Args:
        days: Age threshold in days (files older than this will be deleted)
        
    Returns:
        int: Number of log files deleted
        
    Example:
        >>> deleted = clear_old_logs(days=30)
        >>> print(f"Removed {deleted} old log files")
    """
    logger = get_logger(__name__)
    
    try:
        threshold_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        logger.info(f"Clearing logs older than {days} days (before {threshold_date.date()})")
        
        for log_file in LOG_DIR.glob("spanish_tutor_*.log*"):
            try:
                file_modified = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_modified < threshold_date:
                    log_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old log file: {log_file.name}")
            
            except Exception as e:
                logger.warning(f"Could not delete {log_file.name}: {e}")
        
        logger.info(f"Cleared {deleted_count} old log files")
        return deleted_count
    
    except Exception as e:
        logger.error(f"Error clearing old logs: {e}", exc_info=True)
        return 0


def get_log_stats() -> dict:
    """
    Get statistics about log files.
    
    Returns:
        dict: Dictionary containing log file statistics
        
    Example:
        >>> stats = get_log_stats()
        >>> print(f"Total log size: {stats['total_size_mb']:.2f} MB")
    """
    try:
        log_files = list(LOG_DIR.glob("spanish_tutor_*.log*"))
        total_size = sum(f.stat().st_size for f in log_files)
        
        return {
            'log_count': len(log_files),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'log_directory': str(LOG_DIR),
            'current_log': str(LOG_FILE)
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'log_directory': str(LOG_DIR),
            'current_log': str(LOG_FILE)
        }