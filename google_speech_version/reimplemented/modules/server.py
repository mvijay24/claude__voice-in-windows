#!/usr/bin/env python3
"""
HTTP Server Module
Following Development Guidelines - Modular server handling with error management
"""

import threading
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from .config import config
from .logger import logger
from .error_handler import ErrorHandler, ServerError, with_retry

class SpeechRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler for speech recognition"""
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            if self.path == '/':
                self._serve_main_page()
            elif self.path.startswith('/transcript?'):
                self._handle_transcript()
            elif self.path == '/status':
                self._serve_status()
            else:
                super().do_GET()
        except Exception as e:
            logger.error("Error handling GET request", error=e, path=self.path)
            self._send_error_response(500, "Internal Server Error")
    
    def _serve_main_page(self):
        """Serve the main HTML page"""
        try:
            html_content = self.server.speech_server.get_html_content()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            logger.debug("Served main page")
        except Exception as e:
            logger.error("Error serving main page", error=e)
            self._send_error_response(500, "Could not serve main page")
    
    def _handle_transcript(self):
        """Handle transcript submission"""
        try:
            # Parse transcript from URL
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            text = params.get('text', [''])[0]
            
            if text:
                # Process transcript
                success = self.server.speech_server.process_transcript(text)
                
                if success:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'OK')
                    logger.info("Transcript processed", text_length=len(text))
                else:
                    self._send_error_response(500, "Failed to process transcript")
            else:
                self._send_error_response(400, "No transcript text provided")
        
        except Exception as e:
            logger.error("Error handling transcript", error=e)
            self._send_error_response(500, "Transcript processing failed")
    
    def _serve_status(self):
        """Serve server status for health checks"""
        try:
            status = {
                "status": "running",
                "recording": self.server.speech_server.is_recording
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        except Exception as e:
            logger.error("Error serving status", error=e)
            self._send_error_response(500, "Status check failed")
    
    def _send_error_response(self, code, message):
        """Send error response with proper headers"""
        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(message.encode())
    
    def log_message(self, format, *args):
        """Override to use our logging system"""
        # Only log errors and important requests
        if args[1] != '200' or config.get("logging.level") == "DEBUG":
            logger.debug(f"HTTP: {args[0]} - {args[1]} {args[2]}")

class SpeechServer:
    """Main server class with lifecycle management"""
    
    def __init__(self, html_provider=None, transcript_processor=None):
        self.host = config.get("server.host", "localhost")
        self.port = config.get("server.port", 8899)
        self.httpd = None
        self.server_thread = None
        self.is_running = False
        self.is_recording = False
        
        # Callbacks
        self.html_provider = html_provider
        self.transcript_processor = transcript_processor
        
        logger.info("SpeechServer initialized", host=self.host, port=self.port)
    
    def get_html_content(self):
        """Get HTML content from provider"""
        if self.html_provider:
            return self.html_provider()
        else:
            return "<html><body><h1>Speech Server Running</h1></body></html>"
    
    def process_transcript(self, text):
        """Process transcript through callback"""
        if self.transcript_processor:
            try:
                self.transcript_processor(text)
                return True
            except Exception as e:
                logger.error("Transcript processor failed", error=e)
                return False
        return True
    
    @with_retry(exceptions=(OSError, ServerError))
    def start(self):
        """Start the HTTP server"""
        if self.is_running:
            logger.warning("Server already running")
            return
        
        try:
            # Create HTTP server
            self.httpd = HTTPServer((self.host, self.port), SpeechRequestHandler)
            self.httpd.speech_server = self  # Add reference to self
            
            # Start server in separate thread
            self.server_thread = threading.Thread(
                target=self._run_server,
                daemon=True,
                name="SpeechHTTPServer"
            )
            self.server_thread.start()
            
            self.is_running = True
            logger.info("Server started successfully", url=f"http://{self.host}:{self.port}")
            
        except OSError as e:
            if "Address already in use" in str(e):
                raise ServerError(f"Port {self.port} is already in use")
            raise ServerError(f"Failed to start server: {e}")
    
    def _run_server(self):
        """Run the server (executed in thread)"""
        try:
            logger.debug("Server thread started")
            self.httpd.serve_forever()
        except Exception as e:
            logger.error("Server thread crashed", error=e)
            self.is_running = False
    
    def stop(self):
        """Stop the HTTP server gracefully"""
        if not self.is_running:
            logger.warning("Server not running")
            return
        
        logger.info("Stopping server...")
        
        try:
            # Shutdown the HTTP server
            if self.httpd:
                self.httpd.shutdown()
                self.httpd.server_close()
            
            # Wait for thread to finish
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=config.get("error_handling.shutdown_timeout", 5))
                
                if self.server_thread.is_alive():
                    logger.warning("Server thread did not stop gracefully")
            
            self.is_running = False
            logger.info("Server stopped")
            
        except Exception as e:
            logger.error("Error stopping server", error=e)
    
    def set_recording_state(self, is_recording):
        """Update recording state"""
        self.is_recording = is_recording
        logger.debug(f"Recording state changed to: {is_recording}")
    
    def get_url(self):
        """Get server URL"""
        return f"http://{self.host}:{self.port}"
    
    def is_healthy(self):
        """Check if server is healthy"""
        return self.is_running and self.server_thread and self.server_thread.is_alive()

# Missing import
import json