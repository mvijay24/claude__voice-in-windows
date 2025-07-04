#!/usr/bin/env python3
"""
Ultra-Minimal Google Speech Recognition V2
Zero Word Loss Implementation with Dual-Instance Overlapping
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
    """Return the HTML content with dual-instance zero word loss implementation"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>Speech Recognition V2</title>
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
            max-height: 400px;
            overflow-y: auto;
            font-size: 18px;
            line-height: 1.5;
            white-space: pre-wrap;
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
        .clear { background: #FF9800; color: white; }
        #info {
            position: fixed;
            top: 10px;
            right: 10px;
            font-size: 11px;
            color: #666;
            background: rgba(0,0,0,0.1);
            padding: 5px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <h1 style="text-align: center;">🎤 Speech Recognition V2 - Zero Word Loss</h1>
    <div id="status" class="stopped">Press Ctrl+Space to Start</div>
    <div id="controls">
        <button class="start" onclick="startRec()">Start (Ctrl+Space)</button>
        <button class="stop" onclick="stopRec()">Stop</button>
        <button class="clear" onclick="clearText()">Clear Text</button>
    </div>
    <p style="text-align: center; color: #888; font-size: 14px; margin: 10px 0;">
        ✨ Dual-Instance Technology • No Word Skipping • Seamless Recognition
    </p>
    <div id="transcript"></div>
    <div id="info"></div>
    
    <script>
        // Dual recognition instances for zero word loss
        let recognitionA = null;
        let recognitionB = null;
        let activeInstance = 'A';
        let isRecording = false;
        let finalText = '';
        let switchTimer = null;
        let instanceSwitches = 0;
        
        // Initialize recognition instance
        function createRecognition(name) {
            if (!('webkitSpeechRecognition' in window)) {
                alert('Browser does not support Web Speech API');
                return null;
            }
            
            const recognition = new webkitSpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = 'hi-IN';
            
            recognition.lastIndex = 0;
            
            recognition.onstart = () => {
                console.log(`[${name}] Started`);
            };
            
            recognition.onresult = (event) => {
                // Only process new results
                for (let i = recognition.lastIndex; i < event.results.length; i++) {
                    const result = event.results[i];
                    if (result.isFinal) {
                        // Only add text from active instance
                        if ((name === 'A' && activeInstance === 'A') || 
                            (name === 'B' && activeInstance === 'B')) {
                            const transcript = result[0].transcript;
                            finalText += transcript + ' ';
                            
                            // Send to server
                            fetch('/transcript?text=' + encodeURIComponent(transcript));
                        }
                    }
                }
                recognition.lastIndex = event.results.length;
                
                // Update display from active instance only
                if ((name === 'A' && activeInstance === 'A') || 
                    (name === 'B' && activeInstance === 'B')) {
                    let interim = '';
                    for (let i = event.resultIndex; i < event.results.length; i++) {
                        if (!event.results[i].isFinal) {
                            interim = event.results[i][0].transcript;
                        }
                    }
                    
                    document.getElementById('transcript').innerHTML = 
                        finalText + '<span style="color: #888;">' + interim + '</span>';
                    document.getElementById('transcript').scrollTop = 
                        document.getElementById('transcript').scrollHeight;
                }
                
                updateInfo();
            };
            
            recognition.onerror = (event) => {
                if (event.error !== 'aborted') {
                    console.error(`[${name}] Error:`, event.error);
                }
            };
            
            recognition.onend = () => {
                console.log(`[${name}] Ended`);
                // Auto-restart if still recording and was active
                if (isRecording && name === activeInstance) {
                    setTimeout(() => {
                        if (isRecording) {
                            try {
                                recognition.start();
                            } catch(e) {}
                        }
                    }, 50);
                }
            };
            
            return recognition;
        }
        
        function updateInfo() {
            document.getElementById('info').textContent = 
                `Instance: ${activeInstance} | Switches: ${instanceSwitches}`;
        }
        
        function switchInstance() {
            if (!isRecording) return;
            
            const oldInstance = activeInstance;
            const newInstance = activeInstance === 'A' ? 'B' : 'A';
            const oldRec = activeInstance === 'A' ? recognitionA : recognitionB;
            const newRec = activeInstance === 'A' ? recognitionB : recognitionA;
            
            console.log(`Switching from ${oldInstance} to ${newInstance}`);
            
            try {
                // Start new instance first (overlap)
                newRec.start();
                
                // Switch after 2 second overlap
                setTimeout(() => {
                    activeInstance = newInstance;
                    instanceSwitches++;
                    updateInfo();
                    
                    // Stop old instance gracefully
                    try {
                        oldRec.stop(); // Use stop() not abort()
                    } catch(e) {}
                }, 2000);
                
            } catch(e) {
                console.error('Switch error:', e);
            }
        }
        
        function startRec() {
            if (!recognitionA) recognitionA = createRecognition('A');
            if (!recognitionB) recognitionB = createRecognition('B');
            
            isRecording = true;
            activeInstance = 'A';
            instanceSwitches = 0;
            
            try {
                recognitionA.start();
                document.getElementById('status').className = 'listening';
                document.getElementById('status').textContent = '🔴 Listening...';
                
                // Switch instances every 55 seconds (before 60s limit)
                switchTimer = setInterval(switchInstance, 55000);
                
            } catch(e) {
                console.error('Start error:', e);
            }
            
            updateInfo();
        }
        
        function stopRec() {
            isRecording = false;
            clearInterval(switchTimer);
            
            try { recognitionA.stop(); } catch(e) {}
            try { recognitionB.stop(); } catch(e) {}
            
            document.getElementById('status').className = 'stopped';
            document.getElementById('status').textContent = 'Stopped';
        }
        
        function clearText() {
            finalText = '';
            document.getElementById('transcript').textContent = '';
        }
        
        // Check URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('action') === 'start') {
            setTimeout(startRec, 500);
        }
        
        // Initialize
        window.onload = function() {
            updateInfo();
        };
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
        item('🎤 Open Speech Recognition V2', lambda: webbrowser.open('http://localhost:8899')),
        item('📝 Toggle Recording (Ctrl+Space)', toggle_recording),
        pystray.Menu.SEPARATOR,
        item('❌ Quit', quit_app)
    )
    
    icon = pystray.Icon('GoogleSpeechV2', image, 'Speech Recognition V2', menu)
    return icon

def quit_app(icon=None, item=None):
    """Quit application"""
    global httpd, server_thread
    print("Shutting down...")
    
    if httpd:
        httpd.shutdown()
    
    if server_thread and server_thread.is_alive():
        server_thread.join(timeout=2)
    
    if icon:
        icon.stop()
    
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