@echo off
echo Starting Google Speech Recognition System Tray...
echo.
echo INSTRUCTIONS:
echo 1. A browser window will open with the speech interface
echo 2. Look for the icon in system tray (bottom-right)
echo 3. Press Ctrl+Space to start/stop recording
echo 4. Speak in Hindi/English - text will auto-paste
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

cd /d "%~dp0"
start pythonw minimal_google_speech.pyw

echo.
echo If nothing happens, running with console for debugging...
timeout /t 5 /nobreak >nul

if not exist "http://localhost:8899" (
    echo Running in debug mode...
    python minimal_google_speech.pyw
    pause
)