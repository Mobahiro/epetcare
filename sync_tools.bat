@echo off
echo ===============================================================
echo  ePetCare Database Sync Tools Launcher
echo ===============================================================
echo.
echo Choose an option:
echo.
echo  1. Run Diagnostics and Fix Issues
echo  2. Migrate Database to Render
echo  3. Start Sync Monitor
echo  4. Open Sync Dashboard
echo  5. Exit
echo.
choice /C 12345 /N /M "Enter your choice (1-5): "

if %ERRORLEVEL% EQU 1 (
    echo.
    echo Running diagnostics and fixing issues...
    python diagnose_db_sync.py
    pause
    goto :menu
)

if %ERRORLEVEL% EQU 2 (
    echo.
    echo Migrating database to Render...
    python migrate_to_render.py
    pause
    goto :menu
)

if %ERRORLEVEL% EQU 3 (
    echo.
    echo Starting sync monitor...
    start "ePetCare Sync Monitor" python monitor_db_sync.py --background
    echo Monitor started in background.
    timeout /t 2 >nul
    goto :menu
)

if %ERRORLEVEL% EQU 4 (
    echo.
    echo Opening sync dashboard...
    start "" python sync_dashboard.py
    echo Dashboard opened in your web browser.
    timeout /t 2 >nul
    goto :menu
)

if %ERRORLEVEL% EQU 5 (
    echo.
    echo Exiting...
    exit /b
)

:menu
cls
%0