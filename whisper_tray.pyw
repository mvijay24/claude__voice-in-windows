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

# API Key - Replace with your own!
API_KEY = "YOUR_API_KEY_HERE"  # Get from https://platform.openai.com/api-keys

class WhisperTray:
    def __init__(self):
        self.recording = False
        self.audio_data = []
        self.sample_rate = 16000
        self.max_duration = 300  # 5 minutes max
        self.icon = None
        self.running = True
        self.start_time = None
        self.output_mode = self.load_settings()  # 'hinglish' or 'english'
        
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    return settings.get('output_mode', 'hinglish')
        except:
            pass
        return 'hinglish'
        
    def save_settings(self):
        """Save settings to file"""
        try:
            with open('settings.json', 'w') as f:
                json.dump({'output_mode': self.output_mode}, f)
        except:
            pass
            
    def toggle_output_mode(self, icon, item):
        """Toggle between Hinglish and English output"""
        self.output_mode = 'english' if self.output_mode == 'hinglish' else 'hinglish'
        self.save_settings()
        self.update_menu()
        
    def create_tray_icon(self):
        """Create system tray icon"""
        # Create icon image
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        
        # Draw mic icon
        draw.ellipse([20, 10, 44, 40], fill='#14ffec')
        draw.rectangle([28, 35, 36, 50], fill='#14ffec')
        draw.rectangle([20, 48, 44, 54], fill='#14ffec')
        
        # Create icon
        self.icon = pystray.Icon("whisper_paste", image, "Whisper Paste - Press Ctrl+Space")
        self.update_menu()
        
    def update_menu(self):
        """Update tray menu with current settings"""
        mode_text = f"✓ Output: {self.output_mode.capitalize()}"
        menu = pystray.Menu(
            pystray.MenuItem("🎤 Whisper Paste", lambda: None, enabled=False),
            pystray.MenuItem("━━━━━━━━━━", lambda: None, enabled=False),
            pystray.MenuItem("Ctrl+Space to Record", lambda: None, enabled=False),
            pystray.MenuItem("━━━━━━━━━━", lambda: None, enabled=False),
            pystray.MenuItem("📝 Output Mode:", lambda: None, enabled=False),
            pystray.MenuItem(f"  {'✓' if self.output_mode == 'hinglish' else '  '} Hinglish (Roman)", 
                           lambda: self.set_mode('hinglish')),
            pystray.MenuItem(f"  {'✓' if self.output_mode == 'english' else '  '} English", 
                           lambda: self.set_mode('english')),
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
        
    def update_icon_status(self, recording=False):
        """Update tray icon based on recording status"""
        if not self.icon:
            return
            
        # Create new icon image
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        
        # Draw mic with color based on status
        color = '#ff0000' if recording else '#14ffec'
        draw.ellipse([20, 10, 44, 40], fill=color)
        draw.rectangle([28, 35, 36, 50], fill=color)
        draw.rectangle([20, 48, 44, 54], fill=color)
        
        # Add recording indicator
        if recording:
            draw.ellipse([48, 8, 58, 18], fill='#ff0000')
            
        self.icon.icon = image
        self.icon.title = f"Recording... [{self.output_mode}]" if recording else f"Whisper Paste - Ctrl+Space [{self.output_mode}]"
        
    def record_audio(self):
        """Record audio until stopped"""
        self.update_icon_status(True)
        
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
            self.update_icon_status(False)
            return None
            
        self.update_icon_status(False)
        
        # Process audio
        if not self.audio_data:
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
        try:
            headers = {'Authorization': f'Bearer {API_KEY}'}
            
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
            else:
                return None
                
        except Exception as e:
            return None
            
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
            
        if not self.recording:
            # Start recording
            thread = threading.Thread(target=self.process_recording)
            thread.start()
        else:
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