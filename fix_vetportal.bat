@echo off
echo ===== ePetCare Vet Portal Quick Fix Tool =====
echo.

REM Check if Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not available. Please install Python first.
    pause
    exit /b 1
)

REM Run the diagnostic tool in quick-fix mode
echo Running quick fix...
python diagnose_db_sync.py --quick-fix

if %errorlevel% neq 0 (
    echo Fix failed. Please contact support.
    pause
    exit /b 1
)

echo.
echo Quick fix completed successfully!
echo.
echo You can now try running vetportal.bat again.
echo.
pause