@echo off
echo ========================================
echo    Google Speech Recognition Tests
echo ========================================
echo.
echo Opening all test options...
echo.

:: Open quick test
start "" "quick_test.html"

:: Wait a bit
timeout /t 2 /nobreak >nul

:: Open standalone version
start "" "standalone_speech.html"

:: Show test guide
start notepad "TEST_GUIDE.md"

echo.
echo ========================================
echo All test files opened!
echo.
echo Try speaking in any window:
echo - "Hello bhai"
echo - "Main code likhna chahta hun"
echo - "Testing Hindi English mix"
echo ========================================
pause