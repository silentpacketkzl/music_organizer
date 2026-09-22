@echo off
setlocal
cd /d "%~dp0"

echo ======================================================================
echo   🎵 Burmese Audio Deduper & Myanglish Cleaner - Web GUI
echo ======================================================================

REM Add bundled bin directory to PATH for fpcalc and ffmpeg
set "PATH=%~dp0bin;%PATH%"

REM Test node.js existence
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js runtime was not found.
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM Verify python existence
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Python 3 was not found in PATH.
    echo The bundled CLI executable in 'bin\burmese-music-cleaner-cli.exe' will be used.
)

echo [INFO] Starting application server on http://localhost:3000...
echo [INFO] Opening default web browser...

start "" "http://localhost:3000"

REM Launch Node production server
if exist "dist\server.cjs" (
    node dist\server.cjs
) else (
    call npm run start
)

pause
