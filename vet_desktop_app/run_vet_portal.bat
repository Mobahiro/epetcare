@echo off 
REM Simple launcher for ePetCare Vet Desktop App 
 
REM Change to the script directory 
cd /d "%~dp0" 
 
REM Create data directory if it doesn't exist 
if not exist data mkdir data 
 
REM Create logs directory if it doesn't exist 
if not exist logs mkdir logs 
 
REM Check if Python is installed 
where python > nul 2>&1 
if %ERRORLEVEL% NEQ 0 ( 
    echo ERROR: Python is not installed. 
    echo Please install Python from https://www.python.org/downloads/ 
    echo Make sure to check "Add Python to PATH" during installation. 
    pause 
    exit /b 1 
) 
 
REM Check if required packages are installed 
python -c "import PySide6" > nul 2>&1 
if %ERRORLEVEL% NEQ 0 ( 
    echo Installing required packages... 
    pip install -r requirements.txt 
) 
 
REM Run the application 
python main.py 
 
if %ERRORLEVEL% NEQ 0 ( 
    echo ERROR: The application exited with an error. 
    echo Running diagnostic script... 
    python debug.py 
    pause 
) 
