#!/usr/bin/env python3
"""
Configurable Logging Module with Rotation
Following Development Guidelines - Configurable logging with levels and rotation
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from .config import config

class Logger:
    """Centralized logging system with rotation and configurable levels"""
    
    def __init__(self, name="GoogleSpeech"):
        self.name = name
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with rotation and formatting"""
        # Create logger
        self.logger = logging.getLogger(self.name)
        
        # Get configuration
        log_enabled = config.get("logging.enabled", True)
        log_level = config.get("logging.level", "INFO")
        log_dir = Path(config.get("logging.log_dir", "logs"))
        max_size_mb = config.get("logging.max_size_mb", 10)
        backup_count = config.get("logging.backup_count", 3)
        log_format = config.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        date_format = config.get("logging.date_format", "%Y-%m-%d %H:%M:%S")
        
        if not log_enabled:
            self.logger.disabled = True
            return
        
        # Set level
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }
        self.logger.setLevel(level_map.get(log_level, logging.INFO))
        
        # Create log directory
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter(log_format, datefmt=date_format)
        simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = log_dir / f"{self.name.lower()}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,  # Convert MB to bytes
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def debug(self, message, **kwargs):
        """Log debug message with context"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message, **kwargs):
        """Log info message with context"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message, **kwargs):
        """Log warning message with context"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message, error=None, **kwargs):
        """Log error message with exception details"""
        if error:
            kwargs['error_type'] = type(error).__name__
            kwargs['error_details'] = str(error)
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def _log_with_context(self, level, message, **context):
        """Log message with additional context"""
        if context:
            # Add context to message
            context_str = " | ".join([f"{k}={v}" for k, v in context.items()])
            message = f"{message} | {context_str}"
        
        self.logger.log(level, message)
    
    def log_function_entry(self, func_name, **params):
        """Log function entry with parameters"""
        param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
        self.debug(f"Entering {func_name}({param_str})")
    
    def log_function_exit(self, func_name, result=None, duration_ms=None):
        """Log function exit with result and duration"""
        extras = {}
        if result is not None:
            extras['result'] = result
        if duration_ms is not None:
            extras['duration_ms'] = duration_ms
        self.debug(f"Exiting {func_name}", **extras)
    
    def set_level(self, level):
        """Dynamically change log level"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }
        if level in level_map:
            self.logger.setLevel(level_map[level])
            self.info(f"Log level changed to {level}")
    
    def cleanup_old_logs(self, days_to_keep=7):
        """Clean up log files older than specified days"""
        log_dir = Path(config.get("logging.log_dir", "logs"))
        if not log_dir.exists():
            return
        
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    self.info(f"Deleted old log file: {log_file.name}")
                except Exception as e:
                    self.error(f"Failed to delete log file: {log_file.name}", error=e)

# Create singleton logger instance
logger = Logger()

# Convenience functions for module-level logging
def debug(message, **kwargs):
    logger.debug(message, **kwargs)

def info(message, **kwargs):
    logger.info(message, **kwargs)

def warning(message, **kwargs):
    logger.warning(message, **kwargs)

def error(message, error=None, **kwargs):
    logger.error(message, error=error, **kwargs)