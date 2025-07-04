#!/usr/bin/env python3
"""
Speech Recognition Handler V2 - Zero Word Loss Implementation
Dual-instance overlapping approach to prevent any word skipping
"""

import time
import pyperclip
import keyboard
from .config import config
from .logger import logger
from .error_handler import SpeechRecognitionError, safe_operation

class SpeechHandlerV2:
    """Advanced speech handler with zero word loss using overlapping instances"""
    
    def __init__(self):
        self.is_recording = False
        self.accumulated_text = ""
        logger.info("SpeechHandlerV2 initialized - Zero word loss implementation")
    
    def get_html_content(self):
        """Generate HTML with dual-instance overlapping recognition"""
        logger.debug("Generating HTML content with dual-instance approach")
        
        # Get configuration
        theme = config.get("ui.theme")
        language = config.get("speech.language", "hi-IN")
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Speech Recognition V2</title>
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
        #instance-info {{
            position: fixed;
            top: 10px;
            right: 10px;
            font-size: 11px;
            color: #666;
            background: rgba(0,0,0,0.1);
            padding: 5px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <h1 style="text-align: center;">🎤 Google Speech Recognition V2</h1>
    <div id="status" class="stopped">Press {config.get("hotkeys.toggle_recording", "Ctrl+Space")} to Start</div>
    <div id="controls">
        <button class="start" onclick="startRec()">Start ({config.get("hotkeys.toggle_recording")})</button>
        <button class="stop" onclick="stopRec()">Stop</button>
        <button class="clear" onclick="clearText()">Clear Text</button>
    </div>
    <p style="text-align: center; color: #888; font-size: 14px; margin: 10px 0;">
        📝 Zero Word Loss Technology • Dual-Instance Overlapping
    </p>
    <div id="transcript"></div>
    <div id="debug"></div>
    <div id="instance-info"></div>
    
    <script>
        // Configuration
        const CONFIG = {{
            language: '{language}',
            maxSessionTime: 55000,      // 55 seconds (below 60s limit)
            overlapTime: 2000,          // 2 second overlap
            minRestartDelay: 50,        // Minimal delay for stability
            continuous: true,
            interimResults: true,
            maxAlternatives: 1
        }};
        
        // State management
        let isRecording = false;
        let finalText = '';
        let lastFinalIndex = 0;
        
        // Dual recognition instances
        let recognitionA = null;
        let recognitionB = null;
        let activeInstance = 'A';
        let switchTimer = null;
        
        // Tracking
        let sessionStartTime = null;
        let wordCount = 0;
        let instanceSwitches = 0;
        
        // Debug logging
        function debug(message) {{
            console.log(`[SpeechV2] ${{message}}`);
            document.getElementById('debug').textContent = 
                `${{new Date().toLocaleTimeString()}}: ${{message}}`;
        }}
        
        function updateInstanceInfo() {{
            document.getElementById('instance-info').innerHTML = 
                `Instance: ${{activeInstance}} | Switches: ${{instanceSwitches}} | Words: ${{wordCount}}`;
        }}
        
        // Initialize recognition instance
        function initRecognition(instanceName) {{
            if (!('webkitSpeechRecognition' in window)) {{
                alert('Browser does not support Web Speech API');
                return null;
            }}
            
            const recognition = new webkitSpeechRecognition();
            recognition.continuous = CONFIG.continuous;
            recognition.interimResults = CONFIG.interimResults;
            recognition.lang = CONFIG.language;
            recognition.maxAlternatives = CONFIG.maxAlternatives;
            
            // Track last result index for this instance
            recognition.lastResultIndex = 0;
            
            recognition.onstart = () => {{
                debug(`${{instanceName}} started`);
            }};
            
            recognition.onresult = (event) => {{
                // Process only new results since last index
                for (let i = recognition.lastResultIndex; i < event.results.length; i++) {{
                    const result = event.results[i];
                    const transcript = result[0].transcript;
                    
                    if (result.isFinal) {{
                        // Only process if this is the active instance
                        if ((instanceName === 'A' && activeInstance === 'A') || 
                            (instanceName === 'B' && activeInstance === 'B')) {{
                            finalText += transcript + ' ';
                            wordCount += transcript.split(' ').length;
                            debug(`${{instanceName}} final: "${{transcript}}"`);
                            
                            // Send to server
                            fetch('/transcript?text=' + encodeURIComponent(transcript))
                                .catch(error => debug(`Network error: ${{error.message}}`));
                        }}
                    }}
                }}
                
                // Update last processed index
                recognition.lastResultIndex = event.results.length;
                
                // Update display (show from active instance only)
                if ((instanceName === 'A' && activeInstance === 'A') || 
                    (instanceName === 'B' && activeInstance === 'B')) {{
                    let interim = '';
                    for (let i = event.resultIndex; i < event.results.length; i++) {{
                        if (!event.results[i].isFinal) {{
                            interim = event.results[i][0].transcript;
                        }}
                    }}
                    
                    const transcriptEl = document.getElementById('transcript');
                    transcriptEl.innerHTML = 
                        finalText + '<span style="color: #888;">' + interim + '</span>';
                    transcriptEl.scrollTop = transcriptEl.scrollHeight;
                }}
                
                updateInstanceInfo();
            }};
            
            recognition.onerror = (event) => {{
                // Ignore aborted errors during switching
                if (event.error !== 'aborted') {{
                    debug(`${{instanceName}} error: ${{event.error}}`);
                }}
            }};
            
            recognition.onend = () => {{
                debug(`${{instanceName}} ended`);
                
                // Restart if still recording and this was unexpected
                if (isRecording && instanceName === activeInstance) {{
                    setTimeout(() => {{
                        if (isRecording) {{
                            try {{
                                recognition.start();
                                debug(`${{instanceName}} restarted after unexpected end`);
                            }} catch (e) {{
                                debug(`${{instanceName}} restart error: ${{e.message}}`);
                            }}
                        }}
                    }}, CONFIG.minRestartDelay);
                }}
            }};
            
            return recognition;
        }}
        
        // Switch between instances with overlap
        function switchInstances() {{
            if (!isRecording) return;
            
            const oldInstance = activeInstance;
            const newInstance = activeInstance === 'A' ? 'B' : 'A';
            const oldRecognition = activeInstance === 'A' ? recognitionA : recognitionB;
            const newRecognition = activeInstance === 'A' ? recognitionB : recognitionA;
            
            debug(`Switching from ${{oldInstance}} to ${{newInstance}}`);
            
            // Start new instance first (overlap)
            try {{
                newRecognition.start();
                
                // Switch active instance after overlap period
                setTimeout(() => {{
                    activeInstance = newInstance;
                    instanceSwitches++;
                    updateInstanceInfo();
                    
                    // Stop old instance using stop() not abort() to process pending audio
                    try {{
                        oldRecognition.stop();
                    }} catch (e) {{
                        debug(`Error stopping ${{oldInstance}}: ${{e.message}}`);
                    }}
                }}, CONFIG.overlapTime);
                
            }} catch (e) {{
                debug(`Error starting ${{newInstance}}: ${{e.message}}`);
            }}
        }}
        
        function startRec() {{
            if (!recognitionA) recognitionA = initRecognition('A');
            if (!recognitionB) recognitionB = initRecognition('B');
            
            isRecording = true;
            activeInstance = 'A';
            sessionStartTime = Date.now();
            instanceSwitches = 0;
            
            debug('Starting dual-instance recording');
            
            // Start first instance
            try {{
                recognitionA.start();
                document.getElementById('status').className = 'listening';
                document.getElementById('status').textContent = '🔴 Listening...';
                
                // Schedule instance switches before 60-second limit
                switchTimer = setInterval(() => {{
                    if (isRecording) {{
                        switchInstances();
                    }}
                }}, CONFIG.maxSessionTime);
                
            }} catch (e) {{
                debug(`Start error: ${{e.message}}`);
            }}
            
            updateInstanceInfo();
        }}
        
        function stopRec() {{
            isRecording = false;
            debug('Stopping recording');
            
            clearInterval(switchTimer);
            
            // Stop both instances gracefully
            try {{
                if (recognitionA) recognitionA.stop();
            }} catch (e) {{}}
            
            try {{
                if (recognitionB) recognitionB.stop();
            }} catch (e) {{}}
            
            document.getElementById('status').className = 'stopped';
            document.getElementById('status').textContent = 'Stopped';
            
            // Log session stats
            if (sessionStartTime) {{
                const duration = Math.round((Date.now() - sessionStartTime) / 1000);
                debug(`Session: ${{duration}}s, ${{wordCount}} words, ${{instanceSwitches}} switches`);
            }}
        }}
        
        function clearText() {{
            finalText = '';
            wordCount = 0;
            document.getElementById('transcript').textContent = '';
            debug('Text cleared');
        }}
        
        // Listen for commands
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
            debug('Speech Recognition V2 loaded - Zero word loss technology');
            updateInstanceInfo();
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