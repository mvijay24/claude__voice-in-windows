#!/usr/bin/env python3
"""
Centralized Configuration Module
Following Development Guidelines - All configurable parameters in one place
"""

import os
import json
from pathlib import Path

# ============== GLOBAL CONFIGURATION PARAMETERS ==============
# All changeable parameters centralized as per Development Guidelines

# Server Configuration
SERVER_HOST = "localhost"
SERVER_PORT = 8899
SERVER_TIMEOUT = 30

# Speech Recognition Settings
SPEECH_LANGUAGE = "hi-IN"
MAX_ALTERNATIVES = 1
CONTINUOUS_MODE = True
INTERIM_RESULTS = True
RESTART_INTERVAL_SECONDS = 10  # Periodic restart to prevent timeout
RECOGNITION_TIMEOUT_MS = 200
MIN_RESTART_DELAY_MS = 10

# UI Configuration
UI_THEME = {
    "background": "#1e1e1e",
    "text_color": "#fff",
    "status_listening": "#4CAF50",
    "status_stopped": "#f44336",
    "transcript_bg": "#2a2a2a",
    "button_start": "#4CAF50",
    "button_stop": "#f44336",
    "button_clear": "#FF9800"
}

# Logging Configuration
LOG_ENABLED = True
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_MAX_SIZE_MB = 10
LOG_BACKUP_COUNT = 3
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# File Paths
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
ICON_PATH = BASE_DIR.parent / "icon.ico"
CONFIG_FILE = BASE_DIR / "config.json"

# Hotkey Configuration
HOTKEY_TOGGLE = "ctrl+space"

# Feature Flags
ENABLE_AUTO_START = True
ENABLE_PRE_WARM = True  # Pre-warm recognition engine on startup
ENABLE_TRAY_ICON = True
ENABLE_BROWSER_AUTO_OPEN = True

# Error Handling
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1
GRACEFUL_SHUTDOWN_TIMEOUT = 5

# Browser Settings
BROWSER_CHECK_INTERVAL_MS = 500

class Config:
    """Configuration manager with file-based override support"""
    
    def __init__(self, config_file=None):
        self.config_file = config_file or CONFIG_FILE
        self.settings = self._load_defaults()
        self._load_from_file()
    
    def _load_defaults(self):
        """Load default configuration from module globals"""
        return {
            "server": {
                "host": SERVER_HOST,
                "port": SERVER_PORT,
                "timeout": SERVER_TIMEOUT
            },
            "speech": {
                "language": SPEECH_LANGUAGE,
                "max_alternatives": MAX_ALTERNATIVES,
                "continuous": CONTINUOUS_MODE,
                "interim_results": INTERIM_RESULTS,
                "restart_interval": RESTART_INTERVAL_SECONDS,
                "recognition_timeout": RECOGNITION_TIMEOUT_MS,
                "min_restart_delay": MIN_RESTART_DELAY_MS
            },
            "ui": {
                "theme": UI_THEME
            },
            "logging": {
                "enabled": LOG_ENABLED,
                "level": LOG_LEVEL,
                "max_size_mb": LOG_MAX_SIZE_MB,
                "backup_count": LOG_BACKUP_COUNT,
                "format": LOG_FORMAT,
                "date_format": LOG_DATE_FORMAT,
                "log_dir": str(LOG_DIR)
            },
            "paths": {
                "base_dir": str(BASE_DIR),
                "icon": str(ICON_PATH)
            },
            "hotkeys": {
                "toggle_recording": HOTKEY_TOGGLE
            },
            "features": {
                "auto_start": ENABLE_AUTO_START,
                "pre_warm": ENABLE_PRE_WARM,
                "tray_icon": ENABLE_TRAY_ICON,
                "browser_auto_open": ENABLE_BROWSER_AUTO_OPEN
            },
            "error_handling": {
                "max_retry_attempts": MAX_RETRY_ATTEMPTS,
                "retry_delay": RETRY_DELAY_SECONDS,
                "shutdown_timeout": GRACEFUL_SHUTDOWN_TIMEOUT
            },
            "browser": {
                "check_interval": BROWSER_CHECK_INTERVAL_MS
            }
        }
    
    def _load_from_file(self):
        """Load configuration overrides from JSON file if exists"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    overrides = json.load(f)
                    self._merge_config(self.settings, overrides)
            except Exception as e:
                # If config file is corrupted, continue with defaults
                print(f"Warning: Could not load config file: {e}")
    
    def _merge_config(self, base, overrides):
        """Recursively merge configuration dictionaries"""
        for key, value in overrides.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key_path, default=None):
        """Get configuration value using dot notation (e.g., 'server.port')"""
        keys = key_path.split('.')
        value = self.settings
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path, value):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        target = self.settings
        
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = value
    
    def save(self):
        """Save current configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def reload(self):
        """Reload configuration from file"""
        self.settings = self._load_defaults()
        self._load_from_file()

# Global config instance
config = Config()