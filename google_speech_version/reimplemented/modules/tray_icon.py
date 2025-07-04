#!/usr/bin/env python3
"""
System Tray Icon Module
Following Development Guidelines - Modular tray icon management
"""

import os
import sys
import threading
from PIL import Image
import pystray
from pystray import MenuItem as item
from .config import config
from .logger import logger
from .error_handler import ErrorHandler, safe_operation

class TrayIcon:
    """System tray icon with menu and controls"""
    
    def __init__(self, on_toggle=None, on_open=None, on_quit=None):
        self.icon = None
        self.icon_thread = None
        self.is_running = False
        
        # Callbacks
        self.on_toggle = on_toggle
        self.on_open = on_open
        self.on_quit = on_quit
        
        # State
        self.is_recording = False
        
        logger.info("TrayIcon initialized")
    
    def _create_icon_image(self):
        """Create or load icon image"""
        icon_path = config.get("paths.icon")
        
        if icon_path and os.path.exists(icon_path):
            try:
                image = Image.open(icon_path)
                logger.debug(f"Loaded icon from {icon_path}")
                return image
            except Exception as e:
                logger.warning(f"Failed to load icon from {icon_path}", error=e)
        
        # Create default icon if file not found
        logger.debug("Creating default icon")
        image = Image.new('RGB', (64, 64), color='green')
        
        # Draw a simple microphone shape
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        # Mic body
        draw.ellipse([20, 10, 44, 40], fill='white')
        # Mic stand
        draw.rectangle([30, 35, 34, 50], fill='white')
        # Mic base
        draw.rectangle([20, 48, 44, 52], fill='white')
        
        return image
    
    def _create_menu(self):
        """Create tray menu"""
        hotkey = config.get("hotkeys.toggle_recording", "Ctrl+Space")
        
        menu_items = []
        
        # Open web interface
        if self.on_open:
            menu_items.append(
                item('🎤 Open Speech Recognition', self._handle_open)
            )
        
        # Toggle recording
        if self.on_toggle:
            toggle_text = f'{"⏹️ Stop" if self.is_recording else "🔴 Start"} Recording ({hotkey})'
            menu_items.append(
                item(toggle_text, self._handle_toggle)
            )
        
        # Separator
        menu_items.append(pystray.Menu.SEPARATOR)
        
        # Settings (placeholder for future)
        menu_items.append(
            item('⚙️ Settings', self._handle_settings, enabled=False)
        )
        
        # About
        menu_items.append(
            item('ℹ️ About', self._handle_about)
        )
        
        # Separator
        menu_items.append(pystray.Menu.SEPARATOR)
        
        # Quit
        menu_items.append(
            item('❌ Quit', self._handle_quit)
        )
        
        return pystray.Menu(*menu_items)
    
    @safe_operation("handle_open")
    def _handle_open(self):
        """Handle open menu item"""
        logger.debug("Open menu item clicked")
        if self.on_open:
            self.on_open()
    
    @safe_operation("handle_toggle")
    def _handle_toggle(self):
        """Handle toggle menu item"""
        logger.debug("Toggle menu item clicked")
        if self.on_toggle:
            self.is_recording = self.on_toggle()
            # Update menu
            self._update_menu()
    
    def _handle_settings(self):
        """Handle settings menu item"""
        logger.debug("Settings menu item clicked")
        # Placeholder for future settings dialog
    
    def _handle_about(self):
        """Handle about menu item"""
        logger.debug("About menu item clicked")
        # Could show a message box here
        logger.info("Google Speech Recognition v1.0 - Reimplemented with best practices")
    
    def _handle_quit(self):
        """Handle quit menu item"""
        logger.debug("Quit menu item clicked")
        self.stop()
        if self.on_quit:
            self.on_quit()
    
    def _update_menu(self):
        """Update menu dynamically"""
        if self.icon:
            self.icon.menu = self._create_menu()
            logger.debug("Menu updated")
    
    def start(self):
        """Start the system tray icon"""
        if self.is_running:
            logger.warning("Tray icon already running")
            return
        
        if not config.get("features.tray_icon", True):
            logger.info("Tray icon disabled in configuration")
            return
        
        try:
            # Create icon
            image = self._create_icon_image()
            menu = self._create_menu()
            
            self.icon = pystray.Icon(
                'GoogleSpeechRecognition',
                image,
                'Google Speech Recognition',
                menu
            )
            
            # Run in separate thread
            self.icon_thread = threading.Thread(
                target=self._run_icon,
                daemon=True,
                name="TrayIconThread"
            )
            self.icon_thread.start()
            
            self.is_running = True
            logger.info("Tray icon started")
            
        except Exception as e:
            logger.error("Failed to start tray icon", error=e)
            raise
    
    def _run_icon(self):
        """Run the icon (executed in thread)"""
        try:
            logger.debug("Tray icon thread started")
            self.icon.run()
        except Exception as e:
            logger.error("Tray icon thread crashed", error=e)
            self.is_running = False
    
    def stop(self):
        """Stop the system tray icon"""
        if not self.is_running:
            logger.warning("Tray icon not running")
            return
        
        logger.info("Stopping tray icon...")
        
        try:
            if self.icon:
                self.icon.stop()
            
            # Wait for thread to finish
            if self.icon_thread and self.icon_thread.is_alive():
                self.icon_thread.join(timeout=2)
                
                if self.icon_thread.is_alive():
                    logger.warning("Tray icon thread did not stop gracefully")
            
            self.is_running = False
            logger.info("Tray icon stopped")
            
        except Exception as e:
            logger.error("Error stopping tray icon", error=e)
    
    def update_recording_state(self, is_recording):
        """Update recording state and menu"""
        self.is_recording = is_recording
        self._update_menu()
        logger.debug(f"Tray icon recording state updated: {is_recording}")
    
    def show_notification(self, title, message):
        """Show system notification"""
        if self.icon and hasattr(self.icon, 'notify'):
            try:
                self.icon.notify(title, message)
                logger.debug(f"Notification shown: {title}")
            except Exception as e:
                logger.warning("Failed to show notification", error=e)