@echo off
echo ========================================
echo Google Speech Recognition - Minimal Version
echo ========================================
echo.

:: Install minimal requirements
echo Installing requirements...
pip install -r requirements_minimal.txt

echo.
echo Starting application...
echo Browser will open with speech recognition interface
echo Use Ctrl+Space to start/stop recording
echo.

:: Run the minimal version
pythonw minimal_google_speech.pyw

if errorlevel 1 (
    echo Running with console for debugging...
    python minimal_google_speech.pyw
    pause
)