@echo off
echo Stopping any existing instances...
taskkill /f /im pythonw.exe 2>nul
taskkill /f /im python.exe 2>nul
timeout /t 1 >nul
echo Starting fresh instance...
start "" /b pythonw whisper_tray.pyw
echo.
echo Whisper Paste started in system tray!
echo This window will close in 2 seconds...
timeout /t 2 >nul
exit