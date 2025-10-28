@echo off
echo AI Finance Assistant - Python Installation Helper
echo ================================================
echo.

echo Checking if Python is installed...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python is already installed!
    python --version
    echo.
    echo Running setup script...
    powershell -ExecutionPolicy Bypass -File setup.ps1
) else (
    echo Python is not installed.
    echo.
    echo Please follow these steps:
    echo 1. Go to https://www.python.org/downloads/
    echo 2. Download Python 3.11 or later
    echo 3. IMPORTANT: Check "Add Python to PATH" during installation
    echo 4. Restart this command prompt after installation
    echo 5. Run this file again
    echo.
    echo Opening Python download page...
    start https://www.python.org/downloads/
    echo.
    pause
)
