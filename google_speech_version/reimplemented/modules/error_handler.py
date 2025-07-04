#!/usr/bin/env python3
"""
Robust Error Handling Module
Following Development Guidelines - Anticipate and gracefully manage failure cases
"""

import time
import functools
import traceback
from pathlib import Path
from contextlib import contextmanager
from .config import config
from .logger import logger

class SpeechRecognitionError(Exception):
    """Base exception for speech recognition errors"""
    pass

class ServerError(Exception):
    """Server-related errors"""
    pass

class ConfigurationError(Exception):
    """Configuration-related errors"""
    pass

class ErrorHandler:
    """Centralized error handling with retry logic and graceful degradation"""
    
    @staticmethod
    def retry(max_attempts=None, delay=None, exceptions=(Exception,), fallback=None):
        """
        Decorator for retrying functions with exponential backoff
        
        Args:
            max_attempts: Maximum retry attempts (uses config if None)
            delay: Initial delay between retries (uses config if None)
            exceptions: Tuple of exceptions to catch
            fallback: Fallback function to call if all retries fail
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                attempts = max_attempts or config.get("error_handling.max_retry_attempts", 3)
                retry_delay = delay or config.get("error_handling.retry_delay", 1)
                
                last_error = None
                for attempt in range(attempts):
                    try:
                        logger.debug(f"Attempting {func.__name__} (attempt {attempt + 1}/{attempts})")
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_error = e
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}",
                            error=e,
                            attempts_remaining=attempts - attempt - 1
                        )
                        
                        if attempt < attempts - 1:
                            sleep_time = retry_delay * (2 ** attempt)  # Exponential backoff
                            logger.debug(f"Waiting {sleep_time}s before retry")
                            time.sleep(sleep_time)
                
                # All retries failed
                logger.error(f"All retry attempts failed for {func.__name__}", error=last_error)
                
                if fallback:
                    logger.info(f"Using fallback for {func.__name__}")
                    return fallback(*args, **kwargs)
                
                raise last_error
            
            return wrapper
        return decorator
    
    @staticmethod
    @contextmanager
    def graceful_degradation(operation_name, default_return=None, reraise=False):
        """
        Context manager for graceful degradation of operations
        
        Args:
            operation_name: Name of the operation for logging
            default_return: Value to return if operation fails
            reraise: Whether to re-raise the exception after logging
        """
        try:
            logger.debug(f"Starting operation: {operation_name}")
            yield
            logger.debug(f"Completed operation: {operation_name}")
        except Exception as e:
            logger.error(
                f"Operation failed: {operation_name}",
                error=e,
                traceback=traceback.format_exc()
            )
            
            if reraise:
                raise
            
            return default_return
    
    @staticmethod
    def handle_critical_error(error, component_name, shutdown_func=None):
        """
        Handle critical errors that require system shutdown
        
        Args:
            error: The exception that occurred
            component_name: Name of the component that failed
            shutdown_func: Optional function to call for graceful shutdown
        """
        logger.error(
            f"CRITICAL ERROR in {component_name}",
            error=error,
            traceback=traceback.format_exc()
        )
        
        if shutdown_func:
            logger.info(f"Initiating graceful shutdown due to critical error in {component_name}")
            try:
                shutdown_func()
            except Exception as shutdown_error:
                logger.error("Error during shutdown", error=shutdown_error)
    
    @staticmethod
    def validate_config():
        """Validate configuration and provide helpful error messages"""
        errors = []
        
        # Check required paths
        icon_path = config.get("paths.icon")
        if icon_path and not Path(icon_path).exists():
            logger.warning(f"Icon file not found at {icon_path}, using default")
        
        # Check port availability
        port = config.get("server.port")
        if port < 1024:
            errors.append(f"Port {port} requires admin privileges. Use port >= 1024")
        
        # Check log directory permissions
        log_dir = Path(config.get("logging.log_dir"))
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            test_file = log_dir / ".test"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            errors.append(f"Cannot write to log directory: {e}")
        
        if errors:
            error_msg = "Configuration errors found:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ConfigurationError(error_msg)
        
        logger.info("Configuration validation passed")

# Convenience decorators
def with_retry(max_attempts=None, delay=None, exceptions=(Exception,)):
    """Convenience decorator for retry logic"""
    return ErrorHandler.retry(max_attempts, delay, exceptions)

def safe_operation(operation_name, default_return=None):
    """Decorator for safe operations with graceful degradation"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with ErrorHandler.graceful_degradation(operation_name, default_return):
                return func(*args, **kwargs)
        return wrapper
    return decorator