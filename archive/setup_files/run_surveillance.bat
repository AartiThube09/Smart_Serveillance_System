@echo off
title Smart Surveillance System
cls

echo ================================
echo   Smart Surveillance System
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "surveillance_gui.py" (
    echo Error: surveillance_gui.py not found
    echo Please run this script from the project directory
    pause
    exit /b 1
)

echo Starting Smart Surveillance System...
echo.

REM Try to run the GUI version first
python surveillance_gui.py

REM If GUI fails, try integrated version
if errorlevel 1 (
    echo.
    echo GUI mode failed, trying integrated mode...
    python integrated_surveillance.py
)

echo.
echo System shutdown complete.
pause