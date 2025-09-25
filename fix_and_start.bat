@echo off
echo ===================================================
echo ePetCare Render Connection - Quick Fix
echo ===================================================
echo.
echo This script will:
echo 1. Fix database corruption issues
echo 2. Update the API URL configuration
echo 3. Test the connection to the Render API
echo 4. Launch the vet portal application
echo.
echo ===================================================
echo.
pause

cls
echo ===================================================
echo Step 1: Fixing Database Corruption
echo ===================================================
echo.
python fix_render_connection.py
echo.
pause

cls
echo ===================================================
echo Step 2: Updating API URL Configuration
echo ===================================================
echo.
python update_config.py
echo.
pause

cls
echo ===================================================
echo Step 3: Testing API Connection
echo ===================================================
echo.
python test_api_connection.py
echo.
pause

cls
echo ===================================================
echo Step 4: Launching Vet Portal Application
echo ===================================================
echo.
echo The application will now start. If you encounter any issues,
echo please refer to RENDER_CONNECTION_GUIDE.md for more help.
echo.
pause

call vetportal_fixed.bat