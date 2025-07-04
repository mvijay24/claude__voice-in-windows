@echo off
REM Run Google Speech Recognition V2 - Zero Word Loss Implementation

echo ============================================
echo Google Speech Recognition V2
echo Zero Word Loss Technology
echo ============================================
echo.
echo Features:
echo - No more word skipping!
echo - Dual-instance overlapping
echo - 55-second cycles (not 10s)
echo - Seamless recognition
echo.
echo Starting V2...

python minimal_google_speech_v2.pyw

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start V2
    echo Make sure Python and dependencies are installed
    pause
)