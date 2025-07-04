@echo off
REM Run Google Speech Recognition - Reimplemented Version
REM Following Development Guidelines

echo ==========================================
echo Google Speech Recognition - Reimplemented
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist ".deps_installed" (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo. > .deps_installed
)

REM Run the application
echo Starting application...
python main.py

if errorlevel 1 (
    echo.
    echo ERROR: Application crashed
    pause
)