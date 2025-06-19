@echo off
echo Building System Tray EXE...
pip install pyinstaller
pyinstaller --onefile --windowed --noconsole --icon=icon.ico --name=WhisperPaste --hidden-import=pystray._win32 whisper_tray.pyw
echo.
echo Done! Check dist folder for WhisperPaste.exe
echo The EXE will run silently in system tray.
pause