@echo off
echo ===== ePetCare Indentation Fix Tool =====
echo.
echo This tool specifically fixes the "unexpected indent" error in remote_db_client.py line 228
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not available. Please install Python first.
    pause
    exit /b 1
)

REM Run the fixer script
python fix_indentation.py

if %errorlevel% neq 0 (
    echo.
    echo Fix failed. Please try running the full repair with fix_epetcare.bat
    pause
    exit /b 1
)

echo.
echo Indentation fix completed!
echo You can now try running vetportal.bat again.
echo.
pause