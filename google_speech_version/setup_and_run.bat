@echo off
echo ========================================
echo Google Speech Recognition Setup
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from python.org
    pause
    exit /b 1
)

:: Install requirements
echo Installing required packages...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup complete! Starting application...
echo ========================================
echo.

:: Run the application
pythonw google_speech_tray.pyw

if errorlevel 1 (
    echo ERROR: Failed to start application
    python google_speech_tray.pyw
    pause
)