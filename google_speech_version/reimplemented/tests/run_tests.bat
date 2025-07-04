@echo off
REM Run E2E Tests for Google Speech Recognition
REM Following Development Guidelines - Strategic E2E testing

echo ==========================================
echo Running E2E Tests
echo ==========================================

REM Install test dependencies
python -m pip install pytest pytest-asyncio selenium requests

REM Run tests
python -m pytest test_e2e_speech_recognition.py -v --tb=short

pause