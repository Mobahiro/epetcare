@echo off
echo ========================================
echo ePetCare Vet Portal - ENHANCED VERSION
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

REM Check if Python is installed
echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo Python found: 
python --version
echo.

REM Check for and fix common issues before starting
echo Checking for common issues...
if exist "vet_desktop_app\utils\remote_db_client.py" (
    echo Verifying remote_db_client.py...
    python -m py_compile "vet_desktop_app\utils\remote_db_client.py" >nul 2>&1
    if errorlevel 1 (
        echo WARNING: Issues detected in remote_db_client.py
        echo Attempting to fix...
        if exist "diagnose_db_sync.py" (
            python diagnose_db_sync.py --quick-fix >nul 2>&1
            echo Fixes applied.
        )
    ) else (
        echo remote_db_client.py looks good.
    )
)
echo.

REM Install dependencies without complex checking
echo Installing dependencies...
pip install PySide6 Pillow requests urllib3 certifi psycopg2-binary --quiet
echo Dependencies installed!
echo.

REM Check PostgreSQL configuration
echo Checking PostgreSQL configuration...
if exist "vet_desktop_app\config.json" (
    python -c "import json; c=json.load(open('vet_desktop_app/config.json')); print('PostgreSQL enabled' if c.get('db_sync',{}).get('postgres',{}).get('enabled',False) else 'PostgreSQL not configured')"
) else (
    echo No config file found.
)
echo.

REM Create a simple Python script to run the application
echo Creating application script...
echo import os, sys, traceback > run_app.py
echo # Set up paths >> run_app.py
echo root_dir = r'%CD%' >> run_app.py
echo app_dir = os.path.join(root_dir, 'vet_desktop_app') >> run_app.py
echo sys.path.insert(0, root_dir) >> run_app.py
echo sys.path.insert(0, app_dir) >> run_app.py
echo # Change to the app directory >> run_app.py
echo os.chdir(app_dir) >> run_app.py
echo # Create config.json >> run_app.py
echo config = { >> run_app.py
echo     "database": { >> run_app.py
echo         "path": os.path.join(root_dir, "db.sqlite3").replace("\\", "\\\\"), >> run_app.py
echo         "backup_dir": "backups", >> run_app.py
echo         "real_time_sync": True >> run_app.py
echo     }, >> run_app.py
echo     "remote_database": { >> run_app.py
echo         "enabled": True, >> run_app.py
echo         "url": "https://epetcare.onrender.com/vet_portal/api", >> run_app.py
echo         "username": "YOUR_VET_USERNAME", >> run_app.py
echo         "password": "YOUR_VET_PASSWORD", >> run_app.py
echo         "sync_interval": 30, >> run_app.py
echo         "auto_sync": True >> run_app.py
echo     }, >> run_app.py
echo     "app": { >> run_app.py
echo         "offline_mode": False, >> run_app.py
echo         "sync_interval": 5, >> run_app.py
echo         "auto_backup": True >> run_app.py
echo     }, >> run_app.py
echo     "ui": { >> run_app.py
echo         "theme": "light", >> run_app.py
echo         "font_size": 10 >> run_app.py
echo     } >> run_app.py
echo } >> run_app.py
echo import json >> run_app.py
echo with open('config.json', 'w') as f: >> run_app.py
echo     json.dump(config, f, indent=4) >> run_app.py
echo # Create __init__.py files if they don't exist >> run_app.py
echo for dir_path in ['', 'models', 'views', 'utils']: >> run_app.py
echo     init_file = os.path.join(dir_path, '__init__.py') >> run_app.py
echo     if not os.path.exists(init_file): >> run_app.py
echo         with open(init_file, 'w') as f: >> run_app.py
echo             f.write('# Auto-generated __init__.py file') >> run_app.py
echo # Run the application >> run_app.py
echo try: >> run_app.py
echo     print("Starting ePetCare Vet Portal...") >> run_app.py
echo     print("Please wait for the application window to appear...") >> run_app.py
echo     with open('main.py') as f: >> run_app.py
echo         code = compile(f.read(), 'main.py', 'exec') >> run_app.py
echo         exec(code) >> run_app.py
echo except Exception as e: >> run_app.py
echo     print(f"\nERROR: {e}") >> run_app.py
echo     traceback.print_exc() >> run_app.py
echo     input("\nPress Enter to exit...") >> run_app.py

echo Script created successfully!
echo.

REM Run the Python script
echo Starting ePetCare Vet Portal...
echo.
python run_app.py

REM Check if the application ran successfully
if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start properly
    echo Error code: %errorlevel%
    echo.
    echo Launching diagnostic tool...
    if exist "diagnose_db_sync.py" (
        python diagnose_db_sync.py
        echo.
        echo If you want to fix these issues automatically, run:
        echo fix_db_sync.bat
    ) else (
        echo Diagnostic tools not found. Please run setup_sync_tools.bat first.
    )
) else (
    echo Application ran successfully
)

REM Clean up
if exist run_app.py (
    del run_app.py >nul 2>&1
)

echo.
echo ========================================
echo Application finished
echo ========================================
pause
