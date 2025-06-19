import os
import sys
import time
import threading
import tempfile
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wav
import requests
import pyperclip
import keyboard
from datetime import datetime
import pystray
from PIL import Image, ImageDraw
import signal
import json
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import webbrowser
import queue

class DebugWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.log_queue = queue.Queue()
        self.stay_on_top = False
        self.running = True
        
    def create_window(self):
        """Create the debug window"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
            
        self.window = tk.Toplevel()
        self.window.title("Whisper Paste - Debug Panel")
        self.window.geometry("800x500")
        self.window.configure(bg='black')
        
        # Set window icon if possible
        try:
            self.window.iconbitmap(default='')
        except:
            pass
            
        # Create toolbar frame
        toolbar = tk.Frame(self.window, bg='#1a1a1a', height=40)
        toolbar.pack(fill='x', padx=2, pady=2)
        
        # Clear button
        clear_btn = tk.Button(toolbar, text="Clear Logs", command=self.clear_logs,
                            bg='#2a2a2a', fg='#00ff00', font=('Consolas', 10),
                            relief='flat', padx=10)
        clear_btn.pack(side='left', padx=5, pady=5)
        
        # Stay on top toggle
        self.top_var = tk.BooleanVar(value=self.stay_on_top)
        top_check = tk.Checkbutton(toolbar, text="Stay on Top", variable=self.top_var,
                                  command=self.toggle_on_top, bg='#1a1a1a', fg='#00ff00',
                                  font=('Consolas', 10), selectcolor='#1a1a1a',
                                  activebackground='#1a1a1a', activeforeground='#00ff00')
        top_check.pack(side='left', padx=20)
        
        # Status label
        self.status_label = tk.Label(toolbar, text="Debug Panel Active", 
                                   bg='#1a1a1a', fg='#00ff00', font=('Consolas', 10))
        self.status_label.pack(side='right', padx=10)
        
        # Create scrolled text widget
        self.text_widget = scrolledtext.ScrolledText(
            self.window, 
            wrap=tk.WORD,
            bg='black',
            fg='#00ff00',
            font=('Consolas', 10),
            insertbackground='#00ff00',
            selectbackground='#00ff00',
            selectforeground='black',
            relief='flat',
            borderwidth=5
        )
        self.text_widget.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Configure text tags for different log levels
        self.text_widget.tag_config('timestamp', foreground='#888888')
        self.text_widget.tag_config('info', foreground='#00ff00')
        self.text_widget.tag_config('warning', foreground='#ffff00')
        self.text_widget.tag_config('error', foreground='#ff0000')
        self.text_widget.tag_config('debug', foreground='#00ffff')
        self.text_widget.tag_config('success', foreground='#00ff88')
        
        # Make text widget read-only
        self.text_widget.bind("<Key>", lambda e: "break")
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Start log processor
        self.process_logs()
        
        # Initial log
        self.parent.log("Debug panel opened", "success")
        
    def hide_window(self):
        """Hide the debug window without destroying it"""
        if self.window:
            self.window.withdraw()
            self.parent.log("Debug panel minimized", "info")
            
    def show_window(self):
        """Show the debug window"""
        if not self.window or not self.window.winfo_exists():
            self.create_window()
        else:
            self.window.deiconify()
            self.window.lift()
            self.parent.log("Debug panel restored", "info")
            
    def toggle_on_top(self):
        """Toggle stay on top"""
        self.stay_on_top = self.top_var.get()
        if self.window:
            self.window.attributes('-topmost', self.stay_on_top)
            self.parent.log(f"Stay on top: {self.stay_on_top}", "debug")
            
    def clear_logs(self):
        """Clear all logs"""
        if self.text_widget:
            self.text_widget.config(state='normal')
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.config(state='disabled')
            self.parent.log("Logs cleared", "info")
            
    def add_log(self, message, level='info'):
        """Add a log entry to the queue"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_queue.put((timestamp, message, level))
        
    def process_logs(self):
        """Process log queue and update text widget"""
        if not self.window or not self.window.winfo_exists():
            return
            
        try:
            while not self.log_queue.empty():
                timestamp, message, level = self.log_queue.get_nowait()
                
                self.text_widget.config(state='normal')
                
                # Insert timestamp
                self.text_widget.insert(tk.END, f"[{timestamp}] ", 'timestamp')
                
                # Insert message with appropriate tag
                self.text_widget.insert(tk.END, f"{message}\n", level)
                
                # Auto-scroll to bottom
                self.text_widget.see(tk.END)
                
                self.text_widget.config(state='disabled')
                
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Error processing logs: {e}")
            
        # Schedule next update
        if self.running and self.window and self.window.winfo_exists():
            self.window.after(50, self.process_logs)
            
    def destroy(self):
        """Destroy the debug window"""
        self.running = False
        if self.window and self.window.winfo_exists():
            self.window.destroy()

class WhisperTray:
    def __init__(self):
        self.recording = False
        self.processing = False
        self.audio_data = []
        self.sample_rate = 16000
        self.max_duration = 300  # 5 minutes max
        self.icon = None
        self.running = True
        self.start_time = None
        self.settings = self.load_settings()
        self.output_mode = self.settings.get('output_mode', 'hinglish')
        self.api_key = self.settings.get('api_key', '')
        self.debug_enabled = self.settings.get('debug_enabled', False)
        self.debug_window = None
        
        # Initialize debug window if enabled
        if self.debug_enabled:
            self.debug_window = DebugWindow(self)
            
        self.log("WhisperTray initialized", "success")
        self.log(f"Output mode: {self.output_mode}", "info")
        self.log(f"Debug mode: {'Enabled' if self.debug_enabled else 'Disabled'}", "info")
        
        # Check API key on startup
        if not self.api_key:
            self.log("No API key found, showing setup dialog", "warning")
            self.show_api_key_dialog(first_time=True)
        else:
            self.log("API key loaded successfully", "success")
            
    def log(self, message, level='info'):
        """Log a message to the debug window if enabled"""
        if self.debug_enabled and self.debug_window:
            self.debug_window.add_log(message, level)
            
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        return {}
        
    def save_settings(self):
        """Save all settings to file"""
        try:
            self.settings['output_mode'] = self.output_mode
            self.settings['api_key'] = self.api_key
            self.settings['debug_enabled'] = self.debug_enabled
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f, indent=2)
            self.log("Settings saved", "debug")
        except Exception as e:
            self.log(f"Error saving settings: {e}", "error")
            
    def show_api_key_dialog(self, first_time=False):
        """Show dialog to enter API key"""
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        if first_time:
            root.attributes('-topmost', True)
            root.update()
            messagebox.showinfo(
                "Welcome to Whisper Paste!",
                "You need an OpenAI API key to use this app.\n\n"
                "Click OK to enter your API key.\n"
                "You can get one from: https://platform.openai.com/api-keys"
            )
            
        # Create custom dialog
        dialog = tk.Toplevel(root)
        dialog.title("API Key Settings")
        dialog.geometry("500x250")
        dialog.configure(bg='#1a1a1a')
        
        # Make dialog always on top and bring to front
        dialog.attributes('-topmost', True)
        dialog.lift()
        dialog.focus_force()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')
        
        # Make dialog modal
        dialog.transient(root)
        dialog.grab_set()
        
        # Ensure dialog is visible
        dialog.deiconify()
        dialog.update()
        
        # Title
        tk.Label(dialog, text="OpenAI API Key", font=('Arial', 16, 'bold'),
                bg='#1a1a1a', fg='#14ffec').pack(pady=20)
        
        # Instructions
        tk.Label(dialog, text="Enter your OpenAI API key:", font=('Arial', 10),
                bg='#1a1a1a', fg='white').pack()
        
        # API key entry
        key_frame = tk.Frame(dialog, bg='#1a1a1a')
        key_frame.pack(pady=10, padx=20, fill='x')
        
        key_var = tk.StringVar(value=self.api_key)
        key_entry = tk.Entry(key_frame, textvariable=key_var, font=('Arial', 10),
                           bg='#2a2a2a', fg='white', insertbackground='white')
        key_entry.pack(fill='x', ipady=5)
        
        # Show/Hide button
        show_var = tk.BooleanVar(value=False)
        
        def toggle_show():
            if show_var.get():
                key_entry.config(show='')
                show_btn.config(text='Hide')
            else:
                key_entry.config(show='*')
                show_btn.config(text='Show')
                
        show_btn = tk.Button(key_frame, text='Show', command=lambda: [show_var.set(not show_var.get()), toggle_show()],
                           bg='#3a3a3a', fg='white', font=('Arial', 8), width=6)
        show_btn.place(relx=0.95, rely=0.5, anchor='e')
        
        # Buttons frame
        btn_frame = tk.Frame(dialog, bg='#1a1a1a')
        btn_frame.pack(pady=20)
        
        def save_key():
            new_key = key_var.get().strip()
            if new_key:
                self.api_key = new_key
                self.save_settings()
                self.log("API key updated successfully", "success")
                dialog.attributes('-topmost', True)
                dialog.update()
                messagebox.showinfo("Success", "API key saved successfully!")
                dialog.destroy()
                root.destroy()
                self.update_menu()  # Update menu to show connected status
            else:
                self.log("Invalid API key entered", "warning")
                dialog.attributes('-topmost', True)
                dialog.update()
                messagebox.showwarning("Warning", "Please enter a valid API key")
                
        def get_key():
            webbrowser.open("https://platform.openai.com/api-keys")
            
        # Save button
        tk.Button(btn_frame, text="Save", command=save_key,
                 bg='#14ffec', fg='black', font=('Arial', 10, 'bold'),
                 width=10, height=1).pack(side='left', padx=5)
        
        # Get API Key button
        tk.Button(btn_frame, text="Get API Key", command=get_key,
                 bg='#3a3a3a', fg='white', font=('Arial', 10),
                 width=12, height=1).pack(side='left', padx=5)
        
        # Cancel button
        tk.Button(btn_frame, text="Cancel", command=lambda: [dialog.destroy(), root.destroy()],
                 bg='#3a3a3a', fg='white', font=('Arial', 10),
                 width=10, height=1).pack(side='left', padx=5)
        
        # Focus on entry
        key_entry.focus()
        key_entry.select_range(0, 'end')
        
        # Bind Enter key
        dialog.bind('<Return>', lambda e: save_key())
        
        # Wait for dialog
        root.wait_window(dialog)
        
    def create_tray_icon(self):
        """Create system tray icon"""
        # Create icon image with green for ready state
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        
        # Draw mic icon in green (ready state)
        draw.ellipse([20, 10, 44, 40], fill='#00ff00')  # Green
        draw.rectangle([28, 35, 36, 50], fill='#00ff00')
        draw.rectangle([20, 48, 44, 54], fill='#00ff00')
        
        # Create icon
        self.icon = pystray.Icon("whisper_paste", image, "Whisper Paste - Press Ctrl+Space")
        self.update_menu()
        
    def toggle_debug(self):
        """Toggle debug mode on/off"""
        self.debug_enabled = not self.debug_enabled
        self.save_settings()
        
        if self.debug_enabled:
            if not self.debug_window:
                self.debug_window = DebugWindow(self)
            self.debug_window.show_window()
            self.log("Debug mode enabled", "success")
        else:
            if self.debug_window:
                self.debug_window.hide_window()
            self.log("Debug mode disabled", "info")
            
        self.update_menu()
        
    def show_debug_panel(self):
        """Show the debug panel if debug is enabled"""
        if self.debug_enabled and self.debug_window:
            self.debug_window.show_window()
        
    def update_menu(self):
        """Update tray menu with current settings"""
        api_status = "✓ Connected" if self.api_key else "⚠️ No API Key"
        
        menu = pystray.Menu(
            pystray.MenuItem("🎤 Whisper Paste", lambda: None, enabled=False),
            pystray.MenuItem("━━━━━━━━━━", lambda: None, enabled=False),
            pystray.MenuItem(f"API Status: {api_status}", lambda: None, enabled=False),
            pystray.MenuItem("🔑 Set API Key...", self.show_api_key_dialog),
            pystray.MenuItem("━━━━━━━━━━", lambda: None, enabled=False),
            pystray.MenuItem("📝 Output Mode:", lambda: None, enabled=False),
            pystray.MenuItem(f"  {'✓' if self.output_mode == 'hinglish' else '  '} Hinglish (Roman)", 
                           lambda: self.set_mode('hinglish')),
            pystray.MenuItem(f"  {'✓' if self.output_mode == 'english' else '  '} English", 
                           lambda: self.set_mode('english')),
            pystray.MenuItem("━━━━━━━━━━", lambda: None, enabled=False),
            pystray.MenuItem(f"🐛 {'✓' if self.debug_enabled else '  '} Debug Panel", self.toggle_debug),
            pystray.MenuItem("Show Debug Panel", self.show_debug_panel, enabled=self.debug_enabled),
            pystray.MenuItem("━━━━━━━━━━", lambda: None, enabled=False),
            pystray.MenuItem("🟢 Ready | 🔴 Recording | 🔵 Processing", lambda: None, enabled=False),
            pystray.MenuItem("━━━━━━━━━━", lambda: None, enabled=False),
            pystray.MenuItem("Ctrl+Space to Record", lambda: None, enabled=False),
            pystray.MenuItem("━━━━━━━━━━", lambda: None, enabled=False),
            pystray.MenuItem("Exit", self.quit_app)
        )
        self.icon.menu = menu
        
    def set_mode(self, mode):
        """Set output mode"""
        self.output_mode = mode
        self.save_settings()
        self.update_menu()
        self.log(f"Output mode changed to: {mode}", "info")
        
    def quit_app(self, icon=None, item=None):
        """Properly exit the application"""
        self.log("Shutting down Whisper Paste...", "warning")
        self.running = False
        self.recording = False
        self.processing = False
        
        # Destroy debug window if exists
        if self.debug_window:
            self.debug_window.destroy()
            
        # Stop icon
        if self.icon:
            self.icon.stop()
            
        # Remove hotkey
        try:
            keyboard.unhook_all()
        except:
            pass
            
        # Force exit all threads
        os._exit(0)
        
    def update_icon_status(self, state='ready'):
        """Update tray icon based on state: ready, recording, processing"""
        if not self.icon:
            return
            
        self.log(f"Status changed to: {state}", "debug")
            
        # Create new icon image
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        
        # Set color based on state
        if state == 'recording':
            color = '#ff0000'  # Red for recording
            title = f"🔴 Recording... [{self.output_mode}]"
        elif state == 'processing':
            color = '#0088ff'  # Blue for processing
            title = f"🔵 Processing... [{self.output_mode}]"
        else:  # ready
            color = '#00ff00'  # Green for ready
            title = f"🟢 Whisper Paste - Ctrl+Space [{self.output_mode}]"
        
        # Draw mic icon
        draw.ellipse([20, 10, 44, 40], fill=color)
        draw.rectangle([28, 35, 36, 50], fill=color)
        draw.rectangle([20, 48, 44, 54], fill=color)
        
        # Add indicators
        if state == 'recording':
            # Recording dot
            draw.ellipse([48, 8, 58, 18], fill='#ff0000')
        elif state == 'processing':
            # Processing animation (three dots)
            for i in range(3):
                x = 48 + i * 8
                draw.ellipse([x, 8, x + 4, 12], fill='#0088ff')
            
        self.icon.icon = image
        self.icon.title = title
        
    def record_audio(self):
        """Record audio until stopped"""
        self.update_icon_status('recording')
        self.log("Recording started", "info")
        
        self.audio_data = []
        self.recording = True
        self.start_time = time.time()
        
        def callback(indata, frames, time_info, status):
            if self.recording and self.running:
                elapsed = time.time() - self.start_time
                if elapsed < self.max_duration:
                    self.audio_data.append(indata.copy())
                else:
                    self.log(f"Max recording duration ({self.max_duration}s) reached", "warning")
                    self.recording = False
                    
        try:
            with sd.InputStream(samplerate=self.sample_rate, 
                              channels=1, 
                              callback=callback,
                              dtype='float32'):
                while self.recording and self.running:
                    sd.sleep(100)
        except Exception as e:
            self.log(f"Recording error: {str(e)}", "error")
            self.update_icon_status('ready')
            return None
            
        # Don't update to ready yet - will update to processing next
        
        # Process audio
        if not self.audio_data:
            self.log("No audio data captured", "warning")
            self.update_icon_status('ready')
            return None
            
        audio = np.concatenate(self.audio_data, axis=0)
        duration = len(audio) / self.sample_rate
        self.log(f"Recording stopped. Duration: {duration:.2f}s", "info")
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
            
        # Convert to int16
        audio_int16 = (audio * 32767).astype(np.int16)
        wav.write(temp_file, self.sample_rate, audio_int16)
        self.log(f"Audio saved to temp file: {temp_file}", "debug")
        
        return temp_file
        
    def transcribe_file(self, audio_file):
        """Send audio to OpenAI Whisper API"""
        # Update to processing state
        self.processing = True
        self.update_icon_status('processing')
        self.log(f"Starting transcription (mode: {self.output_mode})", "info")
        
        try:
            if not self.api_key:
                self.log("No API key configured", "error")
                self.show_notification("No API key set! Right-click tray icon to add one.")
                return None
                
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            # Different prompts based on mode
            if self.output_mode == 'hinglish':
                prompt = """Transcribe this audio exactly as spoken. Keep Hindi words in Roman script.
Do NOT translate Hindi words to English. 
Examples:
- Keep: bhai, kya, kar, rahe, ho, acha, theek, hai, nahi, jaldi, bhej, de
- Output format: "bhai ye file bhej de jaldi se"
Preserve the original Hinglish mixing."""
                language = 'hi'  # Hindi for better Hinglish recognition
            else:
                prompt = "Transcribe and translate this to English."
                language = 'en'  # English for translation
            
            self.log(f"Sending API request to OpenAI Whisper", "debug")
            
            with open(audio_file, 'rb') as f:
                files = {
                    'file': ('audio.wav', f, 'audio/wav'),
                    'model': (None, 'whisper-1'),
                    'prompt': (None, prompt),
                    'response_format': (None, 'text'),
                    'language': (None, language)
                }
                
                response = requests.post(
                    'https://api.openai.com/v1/audio/transcriptions',
                    headers=headers,
                    files=files,
                    timeout=60
                )
                
            self.log(f"API response status: {response.status_code}", "debug")
                
            if response.status_code == 200:
                text = response.text.strip()
                self.log(f"Transcription received: {text[:100]}...", "success")
                
                # Force romanization if Devanagari detected
                if any('\u0900' <= char <= '\u097F' for char in text):
                    self.log("Devanagari detected, converting to Roman script", "debug")
                    # Comprehensive transliteration map
                    devanagari_to_roman = {
                        # Common words
                        'ब्रो': 'bro', 'भाई': 'bhai', 'ये': 'ye', 'यह': 'yah', 'है': 'hai',
                        'और': 'aur', 'का': 'ka', 'की': 'ki', 'के': 'ke', 'को': 'ko',
                        'से': 'se', 'में': 'mein', 'मैं': 'main', 'पर': 'par', 'तो': 'to',
                        'भेज': 'bhej', 'दे': 'de', 'जल्दी': 'jaldi', 'अच्छा': 'acha',
                        'ठीक': 'theek', 'क्या': 'kya', 'कर': 'kar', 'रहे': 'rahe',
                        'हो': 'ho', 'नहीं': 'nahi', 'हाँ': 'haan', 'कैसे': 'kaise',
                        'कब': 'kab', 'कहाँ': 'kahan', 'क्यों': 'kyon', 'कौन': 'kaun',
                        'इस': 'is', 'उस': 'us', 'यहाँ': 'yahan', 'वहाँ': 'wahan',
                        'अब': 'ab', 'तब': 'tab', 'जब': 'jab', 'सब': 'sab',
                        'कुछ': 'kuch', 'बहुत': 'bahut', 'बस': 'bas', 'ही': 'hi',
                        'भी': 'bhi', 'तुम': 'tum', 'आप': 'aap', 'हम': 'hum',
                        'वो': 'wo', 'वह': 'wah', 'ये': 'ye', 'वे': 'we',
                        'मेरा': 'mera', 'तेरा': 'tera', 'उसका': 'uska', 'अपना': 'apna',
                        'सकता': 'sakta', 'सकते': 'sakte', 'सकती': 'sakti',
                        'चाहिए': 'chahiye', 'होगा': 'hoga', 'होगी': 'hogi',
                        'करना': 'karna', 'देखना': 'dekhna', 'सुनना': 'sunna',
                        'बोलना': 'bolna', 'आना': 'aana', 'जाना': 'jaana',
                        'फाइल': 'file', 'फोन': 'phone', 'मीटिंग': 'meeting'
                    }
                    
                    for hindi, roman in devanagari_to_roman.items():
                        text = text.replace(hindi, roman)
                    
                    # Remove remaining Devanagari
                    text = ''.join(char if not ('\u0900' <= char <= '\u097F') else ' ' for char in text)
                    text = ' '.join(text.split())
                
                # Clean text
                text = text.replace('"', '').replace("'", '').strip()
                self.log(f"Final text: {text}", "info")
                
                return text
            elif response.status_code == 401:
                self.log("API authentication failed - Invalid API key", "error")
                self.show_notification("Invalid API key! Please check your key.")
                return None
            else:
                self.log(f"API error: {response.status_code} - {response.text}", "error")
                return None
                
        except requests.exceptions.Timeout:
            self.log("API request timed out", "error")
            return None
        except Exception as e:
            self.log(f"Transcription error: {str(e)}", "error")
            return None
        finally:
            self.processing = False
            self.update_icon_status('ready')
            
    def show_notification(self, message):
        """Show a simple notification"""
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        root.update()
        messagebox.showwarning("Whisper Paste", message)
        root.destroy()
        
    def show_toast(self, text, duration=3000):
        """Show a toast notification with text preview"""
        def create_toast():
            root = tk.Tk()
            root.withdraw()
            
            toast = tk.Toplevel(root)
            
            # Configure window
            toast.overrideredirect(True)  # Remove window decorations
            toast.attributes('-topmost', True)
            toast.attributes('-alpha', 0.9)  # Slight transparency
            
            # Style
            toast.configure(bg='#1a1a1a')
            
            # Create frame with border
            frame = tk.Frame(toast, bg='#1a1a1a', highlightbackground='#14ffec', 
                           highlightthickness=2, padx=15, pady=10)
            frame.pack()
            
            # Title
            title_label = tk.Label(frame, text="📝 Transcribed Text:", 
                                 font=('Arial', 10, 'bold'), 
                                 bg='#1a1a1a', fg='#14ffec')
            title_label.pack(anchor='w')
            
            # Text preview (truncate if too long)
            preview_text = text[:100] + "..." if len(text) > 100 else text
            text_label = tk.Label(frame, text=preview_text, 
                                font=('Arial', 9), 
                                bg='#1a1a1a', fg='white',
                                wraplength=300, justify='left')
            text_label.pack(anchor='w', pady=(5, 0))
            
            # Status
            status_label = tk.Label(frame, text="✓ Auto-pasting in 1 second...", 
                                  font=('Arial', 8, 'italic'), 
                                  bg='#1a1a1a', fg='#00ff00')
            status_label.pack(anchor='w', pady=(5, 0))
            
            # Update window size
            toast.update_idletasks()
            
            # Position in bottom right corner
            screen_width = toast.winfo_screenwidth()
            screen_height = toast.winfo_screenheight()
            toast_width = toast.winfo_width()
            toast_height = toast.winfo_height()
            
            x = screen_width - toast_width - 20
            y = screen_height - toast_height - 60
            
            toast.geometry(f'+{x}+{y}')
            
            # Fade in effect
            alpha = 0.0
            def fade_in():
                nonlocal alpha
                if alpha < 0.9:
                    alpha += 0.1
                    toast.attributes('-alpha', alpha)
                    toast.after(30, fade_in)
                else:
                    # Start countdown to destroy
                    toast.after(duration, lambda: [toast.destroy(), root.destroy()])
            
            fade_in()
            
            # Keep window alive
            root.mainloop()
            
        # Create toast in thread to not block
        threading.Thread(target=create_toast, daemon=True).start()
        
    def paste_text(self, text):
        """Copy to clipboard and paste"""
        if not text:
            self.log("No text to paste", "warning")
            return
            
        # Copy to clipboard
        pyperclip.copy(text)
        self.log(f"Text copied to clipboard: {text[:50]}...", "debug")
        
        # Small delay
        time.sleep(0.2)
        
        # Paste
        keyboard.press_and_release('ctrl+v')
        self.log("Text pasted via Ctrl+V", "success")
        
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.running:
            return
            
        self.log("Ctrl+Space pressed", "debug")
            
        if not self.api_key:
            self.log("Recording attempted without API key", "warning")
            self.show_api_key_dialog()
            return
            
        if not self.recording and not self.processing:
            # Start recording
            self.log("Starting new recording thread", "debug")
            thread = threading.Thread(target=self.process_recording)
            thread.start()
        elif self.recording:
            # Stop recording
            self.log("Stopping recording", "info")
            self.recording = False
            
    def process_recording(self):
        """Record, transcribe, and paste"""
        self.log("Process recording started", "debug")
        
        # Record
        audio_file = self.record_audio()
        
        if audio_file and self.running:
            # Transcribe
            text = self.transcribe_file(audio_file)
            
            # Clean up
            try:
                os.unlink(audio_file)
                self.log(f"Temp file deleted: {audio_file}", "debug")
            except Exception as e:
                self.log(f"Failed to delete temp file: {e}", "warning")
                
            # Paste
            if text:
                # Show toast with text preview
                self.show_toast(text)
                # Small delay before pasting
                time.sleep(1)
                self.paste_text(text)
            else:
                self.log("No text to paste after transcription", "warning")
        else:
            self.log("Recording failed or was cancelled", "warning")
                
    def run(self):
        """Run the application"""
        # Register hotkey
        keyboard.add_hotkey('ctrl+space', self.toggle_recording)
        self.log("Hotkey registered: Ctrl+Space", "success")
        
        # Show debug window if enabled
        if self.debug_enabled and self.debug_window:
            self.debug_window.show_window()
        
        # Create and run tray icon
        self.create_tray_icon()
        self.log("System tray icon created", "success")
        
        # Run icon (this blocks until quit)
        self.icon.run()
        
def main():
    # Create and run app
    app = WhisperTray()
    app.run()
    
if __name__ == "__main__":
    main()