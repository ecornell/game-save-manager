@echo off
title Save Game Backup Manager
echo.
echo ================================
echo  Save Game Backup Manager
echo ================================
echo.
echo Choose your interface:
echo 1. GUI Version (Recommended)
echo 2. CLI Version
echo 3. Exit
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo Starting GUI version...
    python backup_gui.py
) else if "%choice%"=="2" (
    echo.
    echo Starting CLI version...
    python backup.py
) else if "%choice%"=="3" (
    echo.
    echo Goodbye!
    exit
) else (
    echo.
    echo Invalid choice. Starting GUI version by default...
    python backup_gui.py
)

echo.
pause
