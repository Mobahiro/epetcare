@echo off
echo ========================================
echo ePetCare Vet Portal - Render Connection Setup
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

REM Get the Render URL and credentials
echo Please enter your Render application URL (e.g., https://your-app.onrender.com):
set /p RENDER_URL="> "

echo Please enter the vet username:
set /p VET_USERNAME="> "

echo Please enter the vet password:
set /p VET_PASSWORD="> "

echo.
echo Setting up connection to Render PostgreSQL database...
echo.

REM Create the config.json with Render connection settings
echo {
echo     "database": {
echo         "path": "%CD%\\db.sqlite3",
echo         "backup_dir": "backups",
echo         "real_time_sync": true
echo     },
echo     "remote_database": {
echo         "enabled": true,
echo         "url": "%RENDER_URL%/vet_portal/api",
echo         "username": "%VET_USERNAME%",
echo         "password": "%VET_PASSWORD%",
echo         "sync_interval": 30,
echo         "auto_sync": true
echo     },
echo     "app": {
echo         "offline_mode": false,
echo         "sync_interval": 5,
echo         "auto_backup": true
echo     },
echo     "ui": {
echo         "theme": "light",
echo         "font_size": 10
echo     }
echo } > vet_desktop_app\config.json

echo Configuration file created successfully!

REM Create the data directory if it doesn't exist
if not exist "vet_desktop_app\data" mkdir vet_desktop_app\data
echo Created data directory for local database cache

echo.
echo Testing connection to Render database...
echo.

REM Run the test script to verify the connection
python test_render_connection.py

echo.
echo If the test was successful, you're ready to use the vet portal with Render!
echo.

REM Run the vet portal application
echo Starting ePetCare Vet Portal...
echo.

start vetportal.bat

echo.
echo ========================================
echo Setup completed
echo ========================================
pause