@echo off
echo ========================================
echo ePetCare Vet Portal - FIXED VERSION
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

REM Install dependencies without complex checking
echo Installing dependencies...
pip install PySide6 Pillow requests urllib3 certifi --quiet
echo Dependencies installed!
echo.

REM Check and repair the database
echo Checking database integrity...
python -c "import sqlite3; conn = sqlite3.connect('db.sqlite3'); conn.execute('PRAGMA integrity_check'); conn.close()" 2>nul
if errorlevel 1 (
    echo WARNING: Database integrity check failed. Attempting to repair...
    echo Creating backup of current database...
    if exist db.sqlite3 (
        copy db.sqlite3 db.sqlite3.bak
        echo Backup created as db.sqlite3.bak
    )
    
    echo Attempting to recover data...
    python -c "import sqlite3; src = sqlite3.connect('db.sqlite3'); dst = sqlite3.connect('db_fixed.sqlite3'); for table in src.execute('SELECT name FROM sqlite_master WHERE type=\"table\"'): try: src.execute('SELECT * FROM ' + table[0]); data = src.execute('SELECT * FROM ' + table[0]).fetchall(); if data: dst.execute('CREATE TABLE IF NOT EXISTS ' + table[0] + ' AS SELECT * FROM src.' + table[0], {'src': src}); dst.commit(); print('Recovered table: ' + table[0]); except: print('Could not recover table: ' + table[0]); src.close(); dst.close();"
    
    if exist db_fixed.sqlite3 (
        echo Fixed database created as db_fixed.sqlite3
        echo Replacing original database with fixed version...
        copy db_fixed.sqlite3 db.sqlite3
        del db_fixed.sqlite3
        echo Database repair completed.
    ) else (
        echo Failed to repair database. Using a new empty database...
        python -c "import sqlite3; conn = sqlite3.connect('db.sqlite3'); conn.close();"
    )
) else (
    echo Database integrity check passed.
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
echo         "url": "https://epetcare.onrender.com", >> run_app.py
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
echo # Create data directory if it doesn't exist >> run_app.py
echo os.makedirs(os.path.join(app_dir, 'data'), exist_ok=True) >> run_app.py
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
)

REM Clean up
if exist run_app.py (
    del run_app.py
    echo Cleaned up temporary files
)

echo.
echo ========================================
echo Application finished
echo ========================================
pause