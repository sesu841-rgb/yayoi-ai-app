@echo off
chcp 65001 > nul
echo ========================================================
echo   Simple Transcription Tool - Launcher
echo ========================================================
echo.

echo Checking Python installation...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python first.
    pause
    exit /b
)

echo.
echo Installing/Updating dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b
)

echo.
echo Launching Application...
python transcription_app.py

pause
