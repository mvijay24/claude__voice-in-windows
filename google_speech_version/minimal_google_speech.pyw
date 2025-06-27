#!/usr/bin/env python3
"""
Ultra-Minimal Google Speech Recognition
Simple, robust implementation with all fixes
"""

import os
import sys
import time
import json
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import pyperclip
import keyboard
from PIL import Image
import pystray
from pystray import MenuItem as item
import urllib.parse

# Global variables
is_recording = False
server_thread = None
httpd = None

class SpeechHandler(SimpleHTTPRequestHandler):
    """Handle requests from the web page"""
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(get_html_content().encode())
        elif self.path.startswith('/transcript?'):
            # Parse transcript from URL
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            text = params.get('text', [''])[0]
            
            if text:
                # Copy and paste
                pyperclip.copy(text)
                time.sleep(0.1)
                keyboard.press_and_release('ctrl+v')
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            super().do_GET()
    
    def log_message(self, format, *args):
        # Suppress server logs
        pass

def get_html_content():
    """Return the HTML content with all fixes implemented"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Speech Recognition</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background: #1e1e1e;
            color: #fff;
        }
        #status {
            font-size: 32px;
            margin: 20px 0;
            text-align: center;
        }
        .listening { color: #4CAF50; }
        .stopped { color: #f44336; }
        #transcript {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 10px;
            min-height: 150px;
            font-size: 18px;
            line-height: 1.5;
        }
        #controls {
            text-align: center;
            margin: 20px 0;
        }
        button {
            font-size: 20px;
            padding: 10px 30px;
            margin: 0 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .start { background: #4CAF50; color: white; }
        .stop { background: #f44336; color: white; }
    </style>
</head>
<body>
    <h1 style="text-align: center;">🎤 Google Speech Recognition</h1>
    <div id="status" class="stopped">Press Ctrl+Space to Start</div>
    <div id="controls">
        <button class="start" onclick="startRec()">Start (Ctrl+Space)</button>
        <button class="stop" onclick="stopRec()">Stop</button>
    </div>
    <div id="transcript"></div>
    
    <script>
        let recognition = null;
        let isRecording = false;
        let finalText = '';
        let restartTimer = null;
        let periodicRestartTimer = null;
        let lastActivityTime = Date.now();
        
        // Initialize
        function init() {
            if (!('webkitSpeechRecognition' in window)) {
                alert('Browser does not support Web Speech API');
                return;
            }
            
            recognition = new webkitSpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'hi-IN';
            recognition.maxAlternatives = 1;
            
            recognition.onstart = () => {
                console.log('Started');
                document.getElementById('status').className = 'listening';
                document.getElementById('status').textContent = '🔴 Listening...';
                lastActivityTime = Date.now();
                
                // Clear existing timers
                clearTimeout(restartTimer);
                clearInterval(periodicRestartTimer);
                
                // Restart every 10 seconds to prevent timeout
                periodicRestartTimer = setInterval(() => {
                    if (isRecording) {
                        console.log('Periodic restart to prevent timeout');
                        recognition.stop();
                    }
                }, 10000); // 10 second intervals
            };
            
            recognition.onresult = (event) => {
                lastActivityTime = Date.now();
                let interim = '';
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalText = transcript;
                        // Send to Python
                        fetch('/transcript?text=' + encodeURIComponent(transcript));
                    } else {
                        interim = transcript;
                    }
                }
                document.getElementById('transcript').textContent = finalText || interim;
            };
            
            recognition.onerror = (event) => {
                console.error('Error:', event.error);
                
                // Handle all errors by restarting
                if (isRecording && event.error !== 'aborted') {
                    console.log('Error occurred, restarting...');
                    clearTimeout(restartTimer);
                    clearInterval(periodicRestartTimer);
                    
                    // Restart after short delay
                    restartTimer = setTimeout(() => {
                        if (isRecording) {
                            try {
                                recognition.start();
                            } catch(e) {
                                console.error('Restart error:', e);
                            }
                        }
                    }, 200);
                }
            };
            
            recognition.onend = () => {
                console.log('Ended');
                clearTimeout(restartTimer);
                clearInterval(periodicRestartTimer);
                
                if (isRecording) {
                    // Auto-restart immediately
                    restartTimer = setTimeout(() => {
                        if (isRecording) {
                            try {
                                recognition.start();
                            } catch(e) {
                                console.error('Restart error:', e);
                            }
                        }
                    }, 50); // Very quick restart
                } else {
                    document.getElementById('status').className = 'stopped';
                    document.getElementById('status').textContent = 'Stopped';
                }
            };
        }
        
        function startRec() {
            if (!recognition) init();
            isRecording = true;
            finalText = '';
            document.getElementById('transcript').textContent = '';
            try {
                recognition.start();
            } catch(e) {
                console.error('Start error:', e);
            }
        }
        
        function stopRec() {
            isRecording = false;
            clearTimeout(restartTimer);
            clearInterval(periodicRestartTimer);
            if (recognition) recognition.stop();
        }
        
        // Listen for commands from Python
        window.addEventListener('message', (e) => {
            if (e.data === 'start') startRec();
            else if (e.data === 'stop') stopRec();
        });
        
        // Check URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('action') === 'start') {
            setTimeout(startRec, 500);
        }
        
        // Initialize on load
        window.onload = init;
    </script>
</body>
</html>'''

def start_server():
    """Start local HTTP server"""
    global httpd, server_thread
    httpd = HTTPServer(('localhost', 8899), SpeechHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

def toggle_recording():
    """Toggle recording state"""
    global is_recording
    is_recording = not is_recording
    
    if is_recording:
        # Open browser with start command
        webbrowser.open('http://localhost:8899/?action=start')
    else:
        # Send stop command (would need WebSocket for this)
        # For now, user can click stop button
        pass

def create_tray_icon():
    """Create system tray icon"""
    # Create or load icon
    icon_path = os.path.join(os.path.dirname(__file__), '..', 'icon.ico')
    if os.path.exists(icon_path):
        image = Image.open(icon_path)
    else:
        image = Image.new('RGB', (64, 64), color='green')
    
    menu = pystray.Menu(
        item('🎤 Open Speech Recognition', lambda: webbrowser.open('http://localhost:8899')),
        item('📝 Toggle Recording (Ctrl+Space)', toggle_recording),
        pystray.Menu.SEPARATOR,
        item('❌ Quit', quit_app)
    )
    
    icon = pystray.Icon('GoogleSpeech', image, 'Google Speech Recognition', menu)
    return icon

def quit_app(icon=None, item=None):
    """Quit application"""
    global httpd, server_thread
    print("Shutting down...")
    
    # Stop the HTTP server
    if httpd:
        httpd.shutdown()
    
    # Stop the server thread
    if server_thread and server_thread.is_alive():
        server_thread.join(timeout=2)
    
    # Stop the system tray icon
    if icon:
        icon.stop()
    
    # Exit cleanly
    sys.exit(0)

def main():
    """Main entry point"""
    # Start server
    start_server()
    time.sleep(1)
    
    # Setup hotkey
    keyboard.add_hotkey('ctrl+space', toggle_recording)
    
    # Create and run tray icon
    icon = create_tray_icon()
    
    # Open browser on first run
    webbrowser.open('http://localhost:8899')
    
    # Run icon
    icon.run()

if __name__ == '__main__':
    main()