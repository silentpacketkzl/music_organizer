@echo off
REM 🎵 Launch Burmese Audio Deduper & Myanglish Cleaner Web GUI (Windows)

echo ==========================================================
echo  Starting Burmese Audio Deduper ^& Myanglish Cleaner GUI
echo ==========================================================

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install from https://nodejs.org
    pause
    exit /b 1
)

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install from https://python.org and add to PATH
    pause
    exit /b 1
)

if not exist "node_modules\" (
    echo [INFO] Installing npm dependencies...
    call npm install
)

echo [INFO] Launching Web GUI on http://localhost:3000...
call npm run dev
pause
