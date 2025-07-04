#!/usr/bin/env python3
"""
End-to-End Tests for Google Speech Recognition
Following Development Guidelines - Focus on E2E tests that simulate real user interactions
"""

import time
import pytest
import requests
import subprocess
import pyperclip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config import Config
from modules.logger import Logger

class TestE2ESpeechRecognition:
    """E2E tests simulating real user workflows"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        # Create test config
        cls.test_config = Config(config_file=Path("test_config.json"))
        cls.test_config.set("server.port", 8898)  # Use different port for tests
        cls.test_config.set("logging.enabled", True)
        cls.test_config.set("logging.level", "DEBUG")
        cls.test_config.set("features.browser_auto_open", False)
        cls.test_config.set("features.tray_icon", False)  # Disable tray for tests
        cls.test_config.save()
        
        # Create test logger
        cls.logger = Logger("TestE2E")
        
        # Start the application
        cls.app_process = subprocess.Popen([
            sys.executable, 
            "main.py"
        ], cwd=Path(__file__).parent.parent)
        
        # Wait for server to start
        cls._wait_for_server(timeout=10)
        
        # Setup Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.media_stream_mic': 1  # Allow microphone
        })
        
        cls.driver = webdriver.Chrome(options=options)
        cls.wait = WebDriverWait(cls.driver, 10)
    
    @classmethod
    def teardown_class(cls):
        """Cleanup test environment"""
        # Close browser
        if hasattr(cls, 'driver'):
            cls.driver.quit()
        
        # Stop application
        if hasattr(cls, 'app_process'):
            cls.app_process.terminate()
            cls.app_process.wait(timeout=5)
        
        # Cleanup test config
        test_config_path = Path("test_config.json")
        if test_config_path.exists():
            test_config_path.unlink()
    
    @classmethod
    def _wait_for_server(cls, timeout=10):
        """Wait for server to be ready"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:8898/status")
                if response.status_code == 200:
                    cls.logger.info("Server is ready")
                    return
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(0.5)
        
        raise RuntimeError("Server failed to start within timeout")
    
    def test_01_server_health_check(self):
        """Test that server is running and healthy"""
        response = requests.get("http://localhost:8898/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "running"
        assert "recording" in data
    
    def test_02_web_interface_loads(self):
        """Test that web interface loads correctly"""
        self.driver.get("http://localhost:8898")
        
        # Check page title
        assert "Speech Recognition" in self.driver.title
        
        # Check main elements exist
        status = self.wait.until(
            EC.presence_of_element_located((By.ID, "status"))
        )
        assert "Press" in status.text
        
        # Check control buttons
        start_button = self.driver.find_element(By.CLASS_NAME, "start")
        assert start_button.is_displayed()
        
        stop_button = self.driver.find_element(By.CLASS_NAME, "stop")
        assert stop_button.is_displayed()
        
        clear_button = self.driver.find_element(By.CLASS_NAME, "clear")
        assert clear_button.is_displayed()
    
    def test_03_start_stop_recording(self):
        """Test starting and stopping recording"""
        self.driver.get("http://localhost:8898")
        
        # Click start button
        start_button = self.driver.find_element(By.CLASS_NAME, "start")
        start_button.click()
        
        # Check status changes to listening
        status = self.driver.find_element(By.ID, "status")
        time.sleep(0.5)  # Wait for status update
        assert "Listening" in status.text
        assert "listening" in status.get_attribute("class")
        
        # Click stop button
        stop_button = self.driver.find_element(By.CLASS_NAME, "stop")
        stop_button.click()
        
        # Check status changes to stopped
        time.sleep(0.5)
        assert "Stopped" in status.text
        assert "stopped" in status.get_attribute("class")
    
    def test_04_clear_text_functionality(self):
        """Test clear text button"""
        self.driver.get("http://localhost:8898")
        
        # Inject some text into transcript
        self.driver.execute_script("""
            document.getElementById('transcript').innerHTML = 'Test text';
            finalText = 'Test text';
        """)
        
        # Verify text is present
        transcript = self.driver.find_element(By.ID, "transcript")
        assert transcript.text == "Test text"
        
        # Click clear button
        clear_button = self.driver.find_element(By.CLASS_NAME, "clear")
        clear_button.click()
        
        # Verify text is cleared
        time.sleep(0.2)
        assert transcript.text == ""
    
    def test_05_transcript_submission(self):
        """Test transcript submission to server"""
        # Clear clipboard first
        pyperclip.copy("")
        
        # Submit transcript via API
        test_text = "Hello from E2E test"
        response = requests.get(
            f"http://localhost:8898/transcript?text={test_text}"
        )
        assert response.status_code == 200
        
        # Check clipboard was updated
        time.sleep(0.5)  # Wait for clipboard update
        clipboard_text = pyperclip.paste()
        assert clipboard_text == test_text
    
    def test_06_url_parameter_auto_start(self):
        """Test auto-start via URL parameter"""
        self.driver.get("http://localhost:8898/?action=start")
        
        # Wait for auto-start
        time.sleep(1)
        
        # Check recording started
        status = self.driver.find_element(By.ID, "status")
        assert "Listening" in status.text
    
    def test_07_speech_recognition_restart(self):
        """Test periodic restart mechanism"""
        self.driver.get("http://localhost:8898")
        
        # Start recording
        start_button = self.driver.find_element(By.CLASS_NAME, "start")
        start_button.click()
        
        # Get initial restart count
        initial_count = self.driver.execute_script("""
            return restartCount;
        """)
        
        # Wait for periodic restart (configured to 10 seconds in default)
        time.sleep(11)
        
        # Check restart count increased
        new_count = self.driver.execute_script("""
            return restartCount;
        """)
        
        assert new_count > initial_count
        
        # Stop recording
        stop_button = self.driver.find_element(By.CLASS_NAME, "stop")
        stop_button.click()
    
    def test_08_concurrent_requests(self):
        """Test server handles concurrent requests"""
        import concurrent.futures
        
        def make_request(text):
            return requests.get(f"http://localhost:8898/transcript?text={text}")
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_request, f"Test {i}")
                for i in range(10)
            ]
            
            results = [f.result() for f in futures]
        
        # All requests should succeed
        for response in results:
            assert response.status_code == 200
    
    def test_09_error_handling(self):
        """Test error handling for invalid requests"""
        # Test empty transcript
        response = requests.get("http://localhost:8898/transcript?text=")
        assert response.status_code == 400
        
        # Test invalid endpoint
        response = requests.get("http://localhost:8898/invalid")
        assert response.status_code == 404
    
    def test_10_graceful_degradation(self):
        """Test system continues working under partial failures"""
        # This would test scenarios like:
        # - Clipboard access failure
        # - Keyboard simulation failure
        # - Browser compatibility issues
        # For now, we'll test that the server stays up
        
        # Make a request that might fail
        response = requests.get("http://localhost:8898/transcript?text=" + "x" * 10000)
        
        # Server should still be responsive
        health_response = requests.get("http://localhost:8898/status")
        assert health_response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])