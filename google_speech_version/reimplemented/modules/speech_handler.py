#!/usr/bin/env python3
"""
Speech Recognition Handler Module
Following Development Guidelines - Core speech recognition logic with modular design
"""

import time
import pyperclip
import keyboard
from .config import config
from .logger import logger
from .error_handler import SpeechRecognitionError, safe_operation

class SpeechHandler:
    """Handles speech recognition operations and text processing"""
    
    def __init__(self):
        self.is_recording = False
        self.accumulated_text = ""
        logger.info("SpeechHandler initialized")
    
    def get_html_content(self):
        """Generate HTML content for speech recognition interface"""
        logger.debug("Generating HTML content")
        
        # Get configuration
        theme = config.get("ui.theme")
        language = config.get("speech.language", "hi-IN")
        restart_interval = config.get("speech.restart_interval", 10)
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Speech Recognition</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background: {theme['background']};
            color: {theme['text_color']};
        }}
        #status {{
            font-size: 32px;
            margin: 20px 0;
            text-align: center;
        }}
        .listening {{ color: {theme['status_listening']}; }}
        .stopped {{ color: {theme['status_stopped']}; }}
        #transcript {{
            background: {theme['transcript_bg']};
            padding: 20px;
            border-radius: 10px;
            min-height: 150px;
            max-height: 400px;
            overflow-y: auto;
            font-size: 18px;
            line-height: 1.5;
            white-space: pre-wrap;
        }}
        #controls {{
            text-align: center;
            margin: 20px 0;
        }}
        button {{
            font-size: 20px;
            padding: 10px 30px;
            margin: 0 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        .start {{ background: {theme['button_start']}; color: white; }}
        .stop {{ background: {theme['button_stop']}; color: white; }}
        .clear {{ background: {theme['button_clear']}; color: white; }}
        #debug {{
            position: fixed;
            bottom: 10px;
            right: 10px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1 style="text-align: center;">🎤 Google Speech Recognition</h1>
    <div id="status" class="stopped">Press {config.get("hotkeys.toggle_recording", "Ctrl+Space")} to Start</div>
    <div id="controls">
        <button class="start" onclick="startRec()">Start ({config.get("hotkeys.toggle_recording")})</button>
        <button class="stop" onclick="stopRec()">Stop</button>
        <button class="clear" onclick="clearText()">Clear Text</button>
    </div>
    <p style="text-align: center; color: #888; font-size: 14px; margin: 10px 0;">
        📝 Text will keep adding (append mode) • Use "Clear Text" to reset
    </p>
    <div id="transcript"></div>
    <div id="debug"></div>
    
    <script>
        // Configuration from server
        const CONFIG = {{
            language: '{language}',
            restartInterval: {restart_interval * 1000},
            recognitionTimeout: {config.get("speech.recognition_timeout", 200)},
            minRestartDelay: {config.get("speech.min_restart_delay", 10)},
            continuous: {str(config.get("speech.continuous", True)).lower()},
            interimResults: {str(config.get("speech.interim_results", True)).lower()},
            maxAlternatives: {config.get("speech.max_alternatives", 1)}
        }};
        
        let recognition = null;
        let isRecording = false;
        let finalText = '';
        let restartTimer = null;
        let periodicRestartTimer = null;
        let lastActivityTime = Date.now();
        let isRestarting = false;
        let sessionStartTime = null;
        let restartCount = 0;
        
        // Debug logging
        function debug(message) {{
            console.log(`[Speech] ${{message}}`);
            document.getElementById('debug').textContent = `${{new Date().toLocaleTimeString()}}: ${{message}}`;
        }}
        
        // Initialize speech recognition
        function init() {{
            if (!('webkitSpeechRecognition' in window)) {{
                alert('Browser does not support Web Speech API');
                return;
            }}
            
            debug('Initializing speech recognition');
            
            recognition = new webkitSpeechRecognition();
            recognition.continuous = CONFIG.continuous;
            recognition.interimResults = CONFIG.interimResults;
            recognition.lang = CONFIG.language;
            recognition.maxAlternatives = CONFIG.maxAlternatives;
            
            recognition.onstart = () => {{
                debug('Recognition started');
                document.getElementById('status').className = 'listening';
                document.getElementById('status').textContent = '🔴 Listening...';
                lastActivityTime = Date.now();
                
                if (!sessionStartTime) {{
                    sessionStartTime = Date.now();
                }}
                
                // Clear existing timers
                clearTimeout(restartTimer);
                clearInterval(periodicRestartTimer);
                
                // Restart periodically to prevent timeout
                periodicRestartTimer = setInterval(() => {{
                    if (isRecording && !isRestarting) {{
                        restartCount++;
                        debug(`Periodic restart #${{restartCount}} to prevent timeout`);
                        isRestarting = true;
                        recognition.abort();
                    }}
                }}, CONFIG.restartInterval);
            }};
            
            recognition.onresult = (event) => {{
                lastActivityTime = Date.now();
                let interim = '';
                
                for (let i = event.resultIndex; i < event.results.length; i++) {{
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {{
                        // Append to finalText
                        finalText += transcript + ' ';
                        debug(`Final text: "${{transcript}}"`);
                        
                        // Send to server
                        fetch('/transcript?text=' + encodeURIComponent(transcript))
                            .then(response => {{
                                if (!response.ok) {{
                                    debug(`Server error: ${{response.status}}`);
                                }}
                            }})
                            .catch(error => {{
                                debug(`Network error: ${{error.message}}`);
                            }});
                    }} else {{
                        interim = transcript;
                    }}
                }}
                
                // Update display
                const transcriptEl = document.getElementById('transcript');
                transcriptEl.innerHTML = 
                    finalText + '<span style="color: #888;">' + interim + '</span>';
                transcriptEl.scrollTop = transcriptEl.scrollHeight;
            }};
            
            recognition.onerror = (event) => {{
                debug(`Error: ${{event.error}}`);
                
                // Handle errors by restarting
                if (isRecording && event.error !== 'aborted') {{
                    clearTimeout(restartTimer);
                    clearInterval(periodicRestartTimer);
                    
                    restartTimer = setTimeout(() => {{
                        if (isRecording) {{
                            try {{
                                recognition.start();
                            }} catch(e) {{
                                debug(`Restart error: ${{e.message}}`);
                            }}
                        }}
                    }}, CONFIG.recognitionTimeout);
                }}
            }};
            
            recognition.onend = () => {{
                debug('Recognition ended');
                clearTimeout(restartTimer);
                clearInterval(periodicRestartTimer);
                
                if (isRecording) {{
                    // Instant restart
                    if (isRestarting) {{
                        isRestarting = false;
                        try {{
                            recognition.start();
                        }} catch(e) {{
                            debug(`Instant restart error: ${{e.message}}`);
                            setTimeout(() => {{
                                try {{ recognition.start(); }} catch(e2) {{}}
                            }}, CONFIG.minRestartDelay);
                        }}
                    }} else {{
                        // Unexpected end
                        setTimeout(() => {{
                            if (isRecording) {{
                                try {{
                                    recognition.start();
                                }} catch(e) {{
                                    debug(`Restart error: ${{e.message}}`);
                                }}
                            }}
                        }}, CONFIG.minRestartDelay);
                    }}
                }} else {{
                    document.getElementById('status').className = 'stopped';
                    document.getElementById('status').textContent = 'Stopped';
                    isRestarting = false;
                    
                    // Log session stats
                    if (sessionStartTime) {{
                        const duration = Math.round((Date.now() - sessionStartTime) / 1000);
                        debug(`Session ended: ${{duration}}s, ${{restartCount}} restarts`);
                        sessionStartTime = null;
                        restartCount = 0;
                    }}
                }}
            }};
        }}
        
        function startRec() {{
            if (!recognition) init();
            isRecording = true;
            debug('Starting recording');
            try {{
                recognition.start();
            }} catch(e) {{
                debug(`Start error: ${{e.message}}`);
            }}
        }}
        
        function stopRec() {{
            isRecording = false;
            debug('Stopping recording');
            clearTimeout(restartTimer);
            clearInterval(periodicRestartTimer);
            if (recognition) recognition.stop();
        }}
        
        function clearText() {{
            finalText = '';
            document.getElementById('transcript').textContent = '';
            debug('Text cleared');
        }}
        
        // Listen for commands from Python
        window.addEventListener('message', (e) => {{
            if (e.data === 'start') startRec();
            else if (e.data === 'stop') stopRec();
        }});
        
        // Check URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('action') === 'start') {{
            setTimeout(startRec, 500);
        }}
        
        // Initialize on load
        window.onload = function() {{
            init();
            debug('Page loaded, recognition ready');
            
            // Pre-warm the recognition engine if enabled
            if ({str(config.get("features.pre_warm", True)).lower()}) {{
                setTimeout(() => {{
                    if (!isRecording && recognition) {{
                        try {{
                            debug('Pre-warming recognition engine');
                            recognition.start();
                            setTimeout(() => {{
                                if (!isRecording) recognition.abort();
                            }}, 100);
                        }} catch(e) {{
                            debug(`Pre-warm skipped: ${{e.message}}`);
                        }}
                    }}
                }}, 500);
            }}
        }};
    </script>
</body>
</html>'''
        
        return html
    
    @safe_operation("process_transcript")
    def process_transcript(self, text):
        """Process incoming transcript text"""
        if not text:
            logger.warning("Empty transcript received")
            return
        
        logger.info(f"Processing transcript: {text[:50]}..." if len(text) > 50 else f"Processing transcript: {text}")
        
        try:
            # Copy to clipboard
            pyperclip.copy(text)
            logger.debug("Text copied to clipboard")
            
            # Small delay for clipboard to settle
            time.sleep(0.1)
            
            # Paste using keyboard
            keyboard.press_and_release('ctrl+v')
            logger.debug("Text pasted via keyboard")
            
            # Track accumulated text
            self.accumulated_text += text + " "
            
        except Exception as e:
            logger.error("Failed to process transcript", error=e)
            raise SpeechRecognitionError(f"Transcript processing failed: {e}")
    
    def toggle_recording(self):
        """Toggle recording state"""
        self.is_recording = not self.is_recording
        logger.info(f"Recording toggled: {self.is_recording}")
        return self.is_recording
    
    def clear_accumulated_text(self):
        """Clear accumulated text"""
        self.accumulated_text = ""
        logger.debug("Accumulated text cleared")
    
    def get_accumulated_text(self):
        """Get all accumulated text"""
        return self.accumulated_text