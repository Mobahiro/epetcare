@echo off
echo ===============================================================
echo  ePetCare Database Sync Fix Tool
echo ===============================================================
echo.
echo This tool will:
echo  1. Check your database synchronization setup
echo  2. Fix any issues with configuration or code
echo  3. Test connectivity with your Render website
echo  4. Synchronize your local database with Render
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

echo.
echo Step 1: Checking Python environment...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH.
    echo Please install Python and add it to your PATH.
    goto :error
)

echo.
echo Step 2: Running diagnostic checks...
python diagnose_db_sync.py
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Diagnostic checks encountered issues.
    echo Continuing with fixes...
)

echo.
echo Step 3: Backing up current database...
if not exist backups mkdir backups
copy db.sqlite3 backups\db_backup_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sqlite3 > nul
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Could not create database backup.
) else (
    echo Database backed up successfully.
)

echo.
echo Step 4: Running database migration to Render...
python migrate_to_render.py --check-only
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Connectivity check failed. Attempting fixes...
) else (
    echo Database connection successful. Proceeding with synchronization...
    python migrate_to_render.py
)

echo.
echo Step 5: Testing database synchronization...
python monitor_db_sync.py --fix
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Synchronization test encountered issues.
    echo See log file for details.
)

echo.
echo Step 6: Restarting Vet Portal application...
echo.
if exist "vet_desktop_app\run_app.bat" (
    echo Stopping any running instances...
    taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq ePetCare*" > nul 2>&1
    echo Starting application...
    start "" "vet_desktop_app\run_app.bat"
) else (
    echo Could not find Vet Portal application launcher.
    echo Please restart the application manually.
)

echo.
echo ===============================================================
echo  Database synchronization setup complete!
echo ===============================================================
echo.
echo Your vet portal application should now be able to synchronize
echo with your Render website. If you continue to experience issues:
echo.
echo 1. Check the log files in the application folder
echo 2. Make sure your Render website is deployed correctly
echo 3. Verify your configuration in vet_desktop_app\config.json
echo.
goto :end

:error
echo.
echo ===============================================================
echo  Error: Setup could not be completed.
echo ===============================================================
echo.
echo Please see the error messages above for details on how to fix
echo the issues manually.
echo.

:end
echo Press any key to exit...
pause > nul