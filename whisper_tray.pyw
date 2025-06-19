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
from tkinter import messagebox, simpledialog
import webbrowser

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
        
        # Check API key on startup
        if not self.api_key:
            self.show_api_key_dialog(first_time=True)
            
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
        
    def save_settings(self):
        """Save all settings to file"""
        try:
            self.settings['output_mode'] = self.output_mode
            self.settings['api_key'] = self.api_key
            with open('settings.json', 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass
            
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
                dialog.attributes('-topmost', True)
                dialog.update()
                messagebox.showinfo("Success", "API key saved successfully!")
                dialog.destroy()
                root.destroy()
                self.update_menu()  # Update menu to show connected status
            else:
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
        
    def quit_app(self, icon=None, item=None):
        """Properly exit the application"""
        self.running = False
        self.recording = False
        self.processing = False
        
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
        
        self.audio_data = []
        self.recording = True
        self.start_time = time.time()
        
        def callback(indata, frames, time_info, status):
            if self.recording and self.running:
                elapsed = time.time() - self.start_time
                if elapsed < self.max_duration:
                    self.audio_data.append(indata.copy())
                else:
                    self.recording = False
                    
        try:
            with sd.InputStream(samplerate=self.sample_rate, 
                              channels=1, 
                              callback=callback,
                              dtype='float32'):
                while self.recording and self.running:
                    sd.sleep(100)
        except Exception as e:
            self.update_icon_status('ready')
            return None
            
        # Don't update to ready yet - will update to processing next
        
        # Process audio
        if not self.audio_data:
            self.update_icon_status('ready')
            return None
            
        audio = np.concatenate(self.audio_data, axis=0)
        duration = len(audio) / self.sample_rate
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
            
        # Convert to int16
        audio_int16 = (audio * 32767).astype(np.int16)
        wav.write(temp_file, self.sample_rate, audio_int16)
        
        return temp_file
        
    def transcribe_file(self, audio_file):
        """Send audio to OpenAI Whisper API"""
        # Update to processing state
        self.processing = True
        self.update_icon_status('processing')
        
        try:
            if not self.api_key:
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
                
            if response.status_code == 200:
                text = response.text.strip()
                
                # Force romanization if Devanagari detected
                if any('\u0900' <= char <= '\u097F' for char in text):
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
                
                return text
            elif response.status_code == 401:
                self.show_notification("Invalid API key! Please check your key.")
                return None
            else:
                return None
                
        except Exception as e:
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
        
    def paste_text(self, text):
        """Copy to clipboard and paste"""
        if not text:
            return
            
        # Copy to clipboard
        pyperclip.copy(text)
        
        # Small delay
        time.sleep(0.2)
        
        # Paste
        keyboard.press_and_release('ctrl+v')
        
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.running:
            return
            
        if not self.api_key:
            self.show_api_key_dialog()
            return
            
        if not self.recording and not self.processing:
            # Start recording
            thread = threading.Thread(target=self.process_recording)
            thread.start()
        elif self.recording:
            # Stop recording
            self.recording = False
            
    def process_recording(self):
        """Record, transcribe, and paste"""
        # Record
        audio_file = self.record_audio()
        
        if audio_file and self.running:
            # Transcribe
            text = self.transcribe_file(audio_file)
            
            # Clean up
            try:
                os.unlink(audio_file)
            except:
                pass
                
            # Paste
            if text:
                self.paste_text(text)
                
    def run(self):
        """Run the application"""
        # Register hotkey
        keyboard.add_hotkey('ctrl+space', self.toggle_recording)
        
        # Create and run tray icon
        self.create_tray_icon()
        
        # Run icon (this blocks until quit)
        self.icon.run()
        
def main():
    # Create and run app
    app = WhisperTray()
    app.run()
    
if __name__ == "__main__":
    main()