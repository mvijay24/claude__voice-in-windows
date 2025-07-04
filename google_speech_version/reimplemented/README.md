# Google Speech Recognition - Reimplemented

A robust, modular implementation of Google Speech Recognition for Windows, following best development practices.

## Architecture

This reimplementation follows the Development Guidelines with:

### 1. **Modular Code Architecture**
- `config.py` - Centralized configuration management
- `logger.py` - Configurable logging with rotation
- `error_handler.py` - Robust error handling and retry logic
- `server.py` - HTTP server with proper lifecycle management
- `speech_handler.py` - Core speech recognition logic
- `tray_icon.py` - System tray integration
- `main.py` - Application orchestration

### 2. **Configurable Logging**
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)
- Automatic log rotation (10MB limit, 3 backups)
- Contextual logging with timestamps and values
- Both console and file output

### 3. **Strategic Testing**
- End-to-end tests simulating real user workflows
- Automated browser testing with Selenium
- Concurrent request handling tests
- Error handling and graceful degradation tests

### 4. **Centralized Configuration**
- All settings in one place
- JSON file override support
- Environment-specific configurations
- Feature flags for easy toggling

### 5. **Robust Error Handling**
- Retry logic with exponential backoff
- Graceful degradation under failures
- Comprehensive error logging
- Health checks and auto-recovery

## Features

- **Speech-to-Text**: Uses Google's Web Speech API for Hindi recognition
- **Auto-Paste**: Automatically pastes recognized text at cursor position
- **System Tray**: Convenient system tray icon with menu
- **Hotkey Support**: Global hotkey (Ctrl+Space) to toggle recording
- **Web Interface**: Clean, dark-themed web UI
- **Append Mode**: Text accumulates instead of overwriting
- **Auto-Restart**: Prevents timeout with periodic restarts
- **Pre-warming**: Faster recognition startup

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   # or
   run.bat
   ```

2. The web interface opens automatically
3. Press Ctrl+Space or click "Start" to begin recording
4. Speak in Hindi (or change language in config)
5. Text is automatically pasted at cursor position

## Configuration

Edit `config.json` or modify settings in `modules/config.py`:

```json
{
    "server": {
        "port": 8899
    },
    "speech": {
        "language": "hi-IN",
        "restart_interval": 10
    },
    "logging": {
        "level": "INFO",
        "max_size_mb": 10
    },
    "features": {
        "auto_start": true,
        "tray_icon": true
    }
}
```

## Testing

Run the comprehensive E2E test suite:

```bash
cd tests
run_tests.bat
```

## Logs

Logs are stored in the `logs/` directory with automatic rotation:
- `googlespeech_YYYYMMDD.log` - Main application logs
- Old logs are automatically cleaned up after 7 days

## Error Recovery

The application includes multiple layers of error recovery:
- Automatic server restart on failure
- Speech recognition timeout prevention
- Clipboard operation retries
- Graceful shutdown handling

## Development

The codebase follows these principles:
- Small, focused functions and modules
- Clear separation of concerns
- Comprehensive error handling
- Extensive logging for debugging
- E2E testing focus

## Troubleshooting

1. **Port Already in Use**: Change port in config.json
2. **Microphone Not Working**: Check browser permissions
3. **No Tray Icon**: Check if Pillow is installed correctly
4. **Recognition Stops**: Check logs for timeout errors

## License

Same as original project