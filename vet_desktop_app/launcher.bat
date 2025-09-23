@echo off
REM ePetCare Vet Desktop Launcher
REM This script tries to launch the application in the following order:
REM 1. Compiled executable (if available)
REM 2. Python script (if Python is installed)

REM Change to the script directory
cd /d "%~dp0"

echo ===== ePetCare Vet Desktop Launcher =====

REM Check if compiled executable exists
if exist dist\ePetCare_Vet_Desktop\ePetCare_Vet_Desktop.exe (
    echo Found compiled executable, launching...
    start "" "dist\ePetCare_Vet_Desktop\ePetCare_Vet_Desktop.exe"
    exit /b 0
)

REM Check if Python is installed
where python > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Compiled executable not found and Python is not installed.
    echo Please either:
    echo 1. Build the application using build_windows.bat
    echo 2. Install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Python is installed, check if we have the required packages
echo Checking for required packages...
python -c "import PySide6" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install required packages.
        echo Please run 'pip install -r requirements.txt' manually.
        pause
        exit /b 1
    )
)

REM Create data directory if it doesn't exist
if not exist data mkdir data

REM Copy database if it exists in the parent directory and not already in data
if exist ..\db.sqlite3 (
    if not exist data\db.sqlite3 (
        echo Copying database file...
        copy /Y ..\db.sqlite3 data\db.sqlite3 > nul
        echo Database copied successfully.
    )
)

REM Set PYTHONPATH to include the current directory
set PYTHONPATH=%CD%;%PYTHONPATH%

REM Run the application
echo Starting ePetCare Vet Desktop application...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: The application exited with an error.
    echo Running diagnostic script...
    python debug.py
    pause
    exit /b 1
)

exit /b 0
