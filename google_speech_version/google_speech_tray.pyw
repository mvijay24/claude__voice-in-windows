#!/usr/bin/env python3
"""
Google Speech Recognition System Tray App
Uses Web Speech API (same as Google Docs) - FREE, no API key needed!
"""

import os
import sys
import json
import time
import threading
import pyperclip
import keyboard
import webview
from pathlib import Path
from PIL import Image
import pystray
from pystray import MenuItem as item
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('google_speech.log'),
        logging.StreamHandler()
    ]
)

class SpeechRecognitionApp:
    def __init__(self):
        self.icon = None
        self.window = None
        self.is_recording = False
        self.html_path = Path(__file__).parent / "speech_recognition.html"
        self.icon_path = Path(__file__).parent.parent / "icon.ico"
        
        # Settings
        self.settings = {
            'hotkey': 'ctrl+space',
            'auto_paste': True,
            'language': 'hi-IN'  # Hindi-India for Hinglish
        }
        
        # Load settings if exists
        self.load_settings()
        
        # Create API object for JavaScript to Python communication
        self.api = self
        
    def load_settings(self):
        """Load settings from JSON file"""
        settings_path = Path(__file__).parent / "settings.json"
        if settings_path.exists():
            try:
                with open(settings_path, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
            except Exception as e:
                logging.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to JSON file"""
        settings_path = Path(__file__).parent / "settings.json"
        try:
            with open(settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
    
    def on_transcript(self, text):
        """Called from JavaScript when transcript is ready"""
        logging.info(f"Received transcript: {text}")
        
        if not text or not text.strip():
            return
            
        # Copy to clipboard
        try:
            pyperclip.copy(text.strip())
            logging.info("Text copied to clipboard")
            
            # Auto-paste if enabled
            if self.settings['auto_paste']:
                # Small delay to ensure clipboard is ready
                time.sleep(0.1)
                keyboard.press_and_release('ctrl+v')
                logging.info("Text pasted")
        except Exception as e:
            logging.error(f"Error in paste operation: {e}")
    
    def toggle_recording(self):
        """Toggle recording state"""
        if not self.window:
            logging.error("WebView window not initialized")
            return
            
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start recording"""
        self.is_recording = True
        self.update_icon_color('red')
        
        # Call JavaScript function
        self.window.evaluate_js('startRecording()')
        logging.info("Recording started")
    
    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        self.update_icon_color('green')
        
        # Call JavaScript function
        self.window.evaluate_js('stopRecording()')
        logging.info("Recording stopped")
    
    def update_icon_color(self, color):
        """Update tray icon color"""
        try:
            # For now, just log the color change
            # In production, you'd create different colored icons
            logging.info(f"Icon color changed to: {color}")
        except Exception as e:
            logging.error(f"Error updating icon: {e}")
    
    def show_window(self, icon=None, item=None):
        """Show the WebView window"""
        if self.window:
            self.window.show()
    
    def hide_window(self, icon=None, item=None):
        """Hide the WebView window"""
        if self.window:
            self.window.hide()
    
    def quit_app(self, icon=None, item=None):
        """Quit the application"""
        logging.info("Quitting application")
        if self.window:
            self.window.destroy()
        if self.icon:
            self.icon.stop()
        os._exit(0)
    
    def create_tray_icon(self):
        """Create system tray icon"""
        # Load icon
        if self.icon_path.exists():
            image = Image.open(self.icon_path)
        else:
            # Create a simple icon if not found
            image = Image.new('RGB', (64, 64), color='green')
        
        # Create menu
        menu = pystray.Menu(
            item('🎤 Toggle Recording (Ctrl+Space)', self.toggle_recording, default=True),
            item('📊 Show Debug Window', self.show_window),
            item('🙈 Hide Debug Window', self.hide_window),
            pystray.Menu.SEPARATOR,
            item('⚙️ Language: Hindi-English', lambda: None, enabled=False),
            item('📋 Auto-paste: Enabled', lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            item('❌ Quit', self.quit_app)
        )
        
        # Create icon
        self.icon = pystray.Icon(
            'GoogleSpeechTray',
            image,
            'Google Speech Recognition',
            menu
        )
    
    def run_webview(self):
        """Run the WebView in a separate thread"""
        # Create window
        self.window = webview.create_window(
            'Google Speech Recognition Engine',
            str(self.html_path),
            js_api=self.api,
            width=800,
            height=600,
            hidden=True  # Start hidden
        )
        
        # Start WebView
        webview.start()
    
    def setup_hotkey(self):
        """Setup global hotkey"""
        try:
            keyboard.add_hotkey(self.settings['hotkey'], self.toggle_recording)
            logging.info(f"Hotkey {self.settings['hotkey']} registered")
        except Exception as e:
            logging.error(f"Error setting up hotkey: {e}")
    
    def run(self):
        """Run the application"""
        # Create system tray icon
        self.create_tray_icon()
        
        # Start WebView in separate thread
        webview_thread = threading.Thread(target=self.run_webview, daemon=True)
        webview_thread.start()
        
        # Wait a bit for WebView to initialize
        time.sleep(2)
        
        # Setup hotkey
        self.setup_hotkey()
        
        # Run system tray
        logging.info("Starting system tray application")
        self.icon.run()


def main():
    """Main entry point"""
    try:
        app = SpeechRecognitionApp()
        app.run()
    except Exception as e:
        logging.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()