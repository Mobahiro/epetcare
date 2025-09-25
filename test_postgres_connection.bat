@echo off
echo ===== ePetCare PostgreSQL Connection Tester =====
echo.

REM Change to the script directory
cd /d "%~dp0"
echo Running from: %CD%
echo.

REM Check if Python is available
echo Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not available. Please install Python first.
    pause
    exit /b 1
)

REM Install required dependencies
echo Installing PostgreSQL driver...
pip install psycopg2-binary requests
echo.

REM Run the test script
echo Running PostgreSQL connection test...
python test_postgres.py
echo.

pause