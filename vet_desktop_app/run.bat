@echo off
REM Run the ePetCare Vet Desktop application

REM Change to the script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install or update dependencies
pip install -r requirements.txt

REM Run the application
python main.py

REM Deactivate virtual environment
deactivate
