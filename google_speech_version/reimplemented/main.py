#!/usr/bin/env python3
"""
Main Application Entry Point
Following Development Guidelines - Orchestrates all modules with proper error handling
"""

import sys
import time
import signal
import webbrowser
import keyboard
from pathlib import Path

# Add modules directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.config import config
from modules.logger import logger
from modules.error_handler import ErrorHandler
from modules.server import SpeechServer
from modules.speech_handler_v2 import SpeechHandlerV2 as SpeechHandler
from modules.tray_icon import TrayIcon

class GoogleSpeechApp:
    """Main application class that coordinates all components"""
    
    def __init__(self):
        self.server = None
        self.speech_handler = None
        self.tray_icon = None
        self.is_running = False
        
        logger.info("="*50)
        logger.info("Google Speech Recognition - Starting")
        logger.info("="*50)
        
        # Validate configuration first
        try:
            ErrorHandler.validate_config()
        except Exception as e:
            logger.error("Configuration validation failed", error=e)
            sys.exit(1)
    
    def initialize_components(self):
        """Initialize all application components"""
        logger.info("Initializing components...")
        
        try:
            # Initialize speech handler
            self.speech_handler = SpeechHandler()
            logger.info("Speech handler initialized")
            
            # Initialize server with callbacks
            self.server = SpeechServer(
                html_provider=self.speech_handler.get_html_content,
                transcript_processor=self.speech_handler.process_transcript
            )
            logger.info("Server initialized")
            
            # Initialize tray icon with callbacks
            self.tray_icon = TrayIcon(
                on_toggle=self.toggle_recording,
                on_open=self.open_web_interface,
                on_quit=self.quit_app
            )
            logger.info("Tray icon initialized")
            
        except Exception as e:
            logger.error("Failed to initialize components", error=e)
            self.cleanup()
            raise
    
    def start(self):
        """Start the application"""
        logger.info("Starting application...")
        
        try:
            # Start server
            self.server.start()
            time.sleep(1)  # Give server time to start
            
            # Setup hotkey
            hotkey = config.get("hotkeys.toggle_recording", "ctrl+space")
            keyboard.add_hotkey(hotkey, self.toggle_recording)
            logger.info(f"Hotkey registered: {hotkey}")
            
            # Start tray icon
            if config.get("features.tray_icon", True):
                self.tray_icon.start()
            
            # Open browser on first run
            if config.get("features.browser_auto_open", True):
                time.sleep(0.5)
                self.open_web_interface()
            
            self.is_running = True
            logger.info("Application started successfully")
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Keep application running
            self.run_main_loop()
            
        except Exception as e:
            logger.error("Failed to start application", error=e)
            self.cleanup()
            raise
    
    def run_main_loop(self):
        """Main application loop"""
        logger.info("Entering main loop...")
        
        try:
            while self.is_running:
                # Check server health
                if not self.server.is_healthy():
                    logger.warning("Server unhealthy, attempting restart...")
                    self.server.stop()
                    time.sleep(1)
                    self.server.start()
                
                # Sleep to prevent high CPU usage
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.quit_app()
    
    def toggle_recording(self):
        """Toggle recording state"""
        try:
            is_recording = self.speech_handler.toggle_recording()
            self.server.set_recording_state(is_recording)
            
            if self.tray_icon:
                self.tray_icon.update_recording_state(is_recording)
            
            if is_recording:
                # Open browser with start command
                url = f"{self.server.get_url()}/?action=start"
                webbrowser.open(url)
                logger.info("Recording started, browser opened")
            else:
                logger.info("Recording stopped")
            
            return is_recording
            
        except Exception as e:
            logger.error("Failed to toggle recording", error=e)
            return False
    
    def open_web_interface(self):
        """Open the web interface in browser"""
        try:
            url = self.server.get_url()
            webbrowser.open(url)
            logger.info(f"Opened web interface: {url}")
        except Exception as e:
            logger.error("Failed to open web interface", error=e)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Signal {signum} received, shutting down...")
            self.quit_app()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Windows-specific
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, signal_handler)
    
    def cleanup(self):
        """Cleanup all resources"""
        logger.info("Cleaning up resources...")
        
        # Stop components in reverse order
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception as e:
                logger.error("Error stopping tray icon", error=e)
        
        if self.server:
            try:
                self.server.stop()
            except Exception as e:
                logger.error("Error stopping server", error=e)
        
        # Remove hotkeys
        try:
            keyboard.unhook_all()
        except Exception as e:
            logger.error("Error removing hotkeys", error=e)
        
        # Cleanup old logs
        try:
            logger.cleanup_old_logs(days_to_keep=7)
        except Exception as e:
            logger.error("Error cleaning up logs", error=e)
        
        logger.info("Cleanup completed")
    
    def quit_app(self):
        """Quit the application gracefully"""
        logger.info("Quit requested...")
        self.is_running = False
        self.cleanup()
        logger.info("="*50)
        logger.info("Google Speech Recognition - Stopped")
        logger.info("="*50)
        sys.exit(0)

def main():
    """Main entry point"""
    try:
        # Create and start application
        app = GoogleSpeechApp()
        app.initialize_components()
        app.start()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error("Fatal error", error=e)
        sys.exit(1)

if __name__ == '__main__':
    main()