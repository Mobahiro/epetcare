@echo off
REM Run the ePetCare Vet Desktop application directly without virtual environment

REM Change to the script directory
cd /d "%~dp0"

REM Set PYTHONPATH to include the current directory
set PYTHONPATH=%CD%;%PYTHONPATH%

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

REM Run the application
echo Starting ePetCare Vet Desktop application...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: The application exited with an error.
    echo Please check the error message above.
    pause
)
