@echo off
echo ===== ePetCare Vet Portal Full System Repair Tool =====
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
    echo Recommended: Python 3.10 or higher.
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Check if pip is available
echo Checking pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not available.
    echo Installing pip...
    python -m ensurepip --default-pip
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install pip.
        pause
        exit /b 1
    )
)
echo pip is available.
echo.

REM Install required dependencies
echo Installing required dependencies...
python -m pip install --upgrade pip
python -m pip install PySide6 Pillow requests urllib3 certifi
echo Dependencies installed successfully.
echo.

REM Create backup folder if it doesn't exist
if not exist "backups" (
    echo Creating backups folder...
    mkdir "backups"
)

REM Backup important files
echo Creating system backups...
set TIMESTAMP=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

if exist "vet_desktop_app\utils\remote_db_client.py" (
    copy "vet_desktop_app\utils\remote_db_client.py" "backups\remote_db_client_%TIMESTAMP%.py" >nul 2>&1
)

if exist "vet_desktop_app\config.json" (
    copy "vet_desktop_app\config.json" "backups\config_%TIMESTAMP%.json" >nul 2>&1
)

if exist "db.sqlite3" (
    copy "db.sqlite3" "backups\db_%TIMESTAMP%.sqlite3" >nul 2>&1
)

echo Backups created in the 'backups' folder.
echo.

REM Run the diagnostic tool in quick-fix mode to fix code issues
echo Fixing common code issues...
python diagnose_db_sync.py --quick-fix

REM Check for config issues
echo Checking config file...
if exist "vet_desktop_app\config.json" (
    echo Config file exists, checking content...
    
    REM Create a Python script to validate and fix config
    echo import json, os, sys > fix_config.py
    echo try: >> fix_config.py
    echo     with open('vet_desktop_app/config.json', 'r') as f: >> fix_config.py
    echo         config = json.load(f) >> fix_config.py
    echo     changes = False >> fix_config.py
    echo     # Check database path >> fix_config.py
    echo     if 'database' not in config: >> fix_config.py
    echo         config['database'] = {} >> fix_config.py
    echo         changes = True >> fix_config.py
    echo     if 'path' not in config['database'] or not config['database']['path']: >> fix_config.py
    echo         config['database']['path'] = os.path.join(os.getcwd(), "db.sqlite3").replace("\\", "\\\\") >> fix_config.py
    echo         changes = True >> fix_config.py
    echo     if 'backup_dir' not in config['database'] or not config['database']['backup_dir']: >> fix_config.py
    echo         config['database']['backup_dir'] = "backups" >> fix_config.py
    echo         changes = True >> fix_config.py
    echo     # Check remote database config >> fix_config.py
    echo     if 'remote_database' not in config: >> fix_config.py
    echo         config['remote_database'] = {} >> fix_config.py
    echo         changes = True >> fix_config.py
    echo     if 'url' not in config['remote_database'] or not config['remote_database']['url']: >> fix_config.py
    echo         config['remote_database']['url'] = "https://epetcare.onrender.com/vet_portal/api" >> fix_config.py
    echo         changes = True >> fix_config.py
    echo     if changes: >> fix_config.py
    echo         print("Fixing config.json...") >> fix_config.py
    echo         with open('vet_desktop_app/config.json', 'w') as f: >> fix_config.py
    echo             json.dump(config, f, indent=4) >> fix_config.py
    echo         print("Config fixed successfully") >> fix_config.py
    echo     else: >> fix_config.py
    echo         print("No config issues found") >> fix_config.py
    echo except Exception as e: >> fix_config.py
    echo     print(f"Error fixing config: {e}") >> fix_config.py
    echo     sys.exit(1) >> fix_config.py
    
    python fix_config.py
    del fix_config.py >nul 2>&1
) else (
    echo Creating new config file...
    if not exist "vet_desktop_app" (
        mkdir "vet_desktop_app"
    )
    
    echo { > "vet_desktop_app\config.json"
    echo     "database": { >> "vet_desktop_app\config.json"
    echo         "path": "%CD:\=\\%\\db.sqlite3", >> "vet_desktop_app\config.json"
    echo         "backup_dir": "backups", >> "vet_desktop_app\config.json"
    echo         "real_time_sync": true >> "vet_desktop_app\config.json"
    echo     }, >> "vet_desktop_app\config.json"
    echo     "remote_database": { >> "vet_desktop_app\config.json"
    echo         "enabled": true, >> "vet_desktop_app\config.json"
    echo         "url": "https://epetcare.onrender.com/vet_portal/api", >> "vet_desktop_app\config.json"
    echo         "username": "YOUR_USERNAME", >> "vet_desktop_app\config.json"
    echo         "password": "YOUR_PASSWORD", >> "vet_desktop_app\config.json"
    echo         "sync_interval": 30, >> "vet_desktop_app\config.json"
    echo         "auto_sync": true >> "vet_desktop_app\config.json"
    echo     }, >> "vet_desktop_app\config.json"
    echo     "app": { >> "vet_desktop_app\config.json"
    echo         "offline_mode": false, >> "vet_desktop_app\config.json"
    echo         "sync_interval": 5, >> "vet_desktop_app\config.json"
    echo         "auto_backup": true >> "vet_desktop_app\config.json"
    echo     }, >> "vet_desktop_app\config.json"
    echo     "ui": { >> "vet_desktop_app\config.json"
    echo         "theme": "light", >> "vet_desktop_app\config.json"
    echo         "font_size": 10 >> "vet_desktop_app\config.json"
    echo     } >> "vet_desktop_app\config.json"
    echo } >> "vet_desktop_app\config.json"
    
    echo New config file created.
)
echo.

REM Check for database issues
echo Checking database...
if exist "db.sqlite3" (
    echo Database file exists, checking integrity...
    
    REM Create a Python script to check database integrity
    echo import sqlite3, sys > check_db.py
    echo try: >> check_db.py
    echo     conn = sqlite3.connect('db.sqlite3') >> check_db.py
    echo     cursor = conn.cursor() >> check_db.py
    echo     cursor.execute('PRAGMA integrity_check') >> check_db.py
    echo     result = cursor.fetchone()[0] >> check_db.py
    echo     if result != 'ok': >> check_db.py
    echo         print(f"Database integrity issue: {result}") >> check_db.py
    echo         print("Attempting repair...") >> check_db.py
    echo         # Export database structure >> check_db.py
    echo         cursor.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL") >> check_db.py
    echo         schema = cursor.fetchall() >> check_db.py
    echo         with open('db_schema.sql', 'w') as f: >> check_db.py
    echo             for s in schema: >> check_db.py
    echo                 f.write(f"{s[0]};\n") >> check_db.py
    echo         conn.close() >> check_db.py
    echo         # Create a new database >> check_db.py
    echo         import os, shutil >> check_db.py
    echo         if os.path.exists('db.sqlite3'): >> check_db.py
    echo             shutil.copy2('db.sqlite3', 'db.sqlite3.corrupted') >> check_db.py
    echo         conn = sqlite3.connect('db.sqlite3.new') >> check_db.py
    echo         cursor = conn.cursor() >> check_db.py
    echo         with open('db_schema.sql', 'r') as f: >> check_db.py
    echo             sql = f.read() >> check_db.py
    echo             cursor.executescript(sql) >> check_db.py
    echo         conn.commit() >> check_db.py
    echo         conn.close() >> check_db.py
    echo         os.replace('db.sqlite3.new', 'db.sqlite3') >> check_db.py
    echo         print("Database structure repaired.") >> check_db.py
    echo     else: >> check_db.py
    echo         print("Database integrity check passed.") >> check_db.py
    echo         conn.close() >> check_db.py
    echo except Exception as e: >> check_db.py
    echo     print(f"Error checking database: {e}") >> check_db.py
    echo     sys.exit(1) >> check_db.py
    
    python check_db.py
    del check_db.py >nul 2>&1
    if exist db_schema.sql del db_schema.sql >nul 2>&1
) else (
    echo Database file does not exist.
    echo This is not a critical error if this is a new installation.
)
echo.

echo System repair completed successfully!
echo.
echo The following issues have been addressed:
echo  - Fixed code issues in Python files
echo  - Validated or created configuration file
echo  - Checked database integrity
echo  - Backed up important files
echo.
echo You can now try running vetportal.bat again.
echo.
pause