@echo off
REM Run the ePetCare Vet Desktop application

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is installed
where python > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create virtual environment.
        echo Please make sure you have the venv module available.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install or update dependencies
echo Installing required packages...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Some packages might not have installed correctly.
    echo The application may still work if core dependencies are already installed.
    pause
)

REM Create data directory if it doesn't exist
if not exist data mkdir data

REM Copy database if it exists in the parent directory
if exist ..\db.sqlite3 (
    echo Copying database file...
    copy /Y ..\db.sqlite3 data\db.sqlite3 > nul
    echo Database copied successfully.
)

REM Set PYTHONPATH to include the current directory
set PYTHONPATH=%CD%;%PYTHONPATH%

REM Run the application
echo Starting ePetCare Vet Desktop application...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: The application exited with an error.
    echo Please check the error message above.
    pause
)

REM Deactivate virtual environment
deactivate
