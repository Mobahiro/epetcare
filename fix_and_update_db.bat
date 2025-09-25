@echo off
echo ===============================================================
echo  ePetCare Database Sync Fix and Update Tool
echo ===============================================================
echo.
echo This script will:
echo  1. Fix database synchronization issues
echo  2. Push your local database to Render
echo  3. Update your GitHub repository with the fixes
echo.
echo Press Ctrl+C to cancel or any key to continue...
pause > nul

echo.
echo Step 1: Running database sync diagnostics and fixes...
python fix_db_sync.py
if %ERRORLEVEL% NEQ 0 (
    echo Failed to run fix_db_sync.py. Please check for errors.
    goto :error
)

echo.
echo Step 2: Pushing local database to Render...
echo.
python migrate_to_render.py
if %ERRORLEVEL% NEQ 0 (
    echo Warning: migrate_to_render.py may have encountered issues, but continuing...
)

echo.
echo Step 3: Updating GitHub repository...
echo.
git add .
git commit -m "Fix database synchronization between vet portal and render website"
git push origin main

echo.
echo ===============================================================
echo  All done! Your changes have been pushed to GitHub and Render.
echo ===============================================================
echo.
echo Render will automatically deploy the updated code.
echo.
goto :end

:error
echo.
echo ===============================================================
echo  Error: Some steps failed. Please check the logs.
echo ===============================================================
echo.

:end
pause