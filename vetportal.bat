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

REM Create runner script (will NOT overwrite existing Postgres config)
echo Creating application script...
echo import os, sys, json, traceback > run_app.py
echo root_dir = r'%CD%' >> run_app.py
echo app_dir = os.path.join(root_dir, 'vet_desktop_app') >> run_app.py
echo sys.path.insert(0, root_dir) >> run_app.py
echo sys.path.insert(0, app_dir) >> run_app.py
echo os.chdir(app_dir) >> run_app.py
echo cfg_path = os.path.join(app_dir, 'config.json') >> run_app.py
echo needs_template = False >> run_app.py
echo if not os.path.exists(cfg_path): >> run_app.py
echo     needs_template = True >> run_app.py
echo else: >> run_app.py
echo     try: >> run_app.py
echo         data = json.load(open(cfg_path, 'r')) >> run_app.py
echo         if 'postgres' not in data: >> run_app.py
echo             needs_template = True >> run_app.py
echo     except Exception: >> run_app.py
echo         needs_template = True >> run_app.py
echo if needs_template: >> run_app.py
echo     template = { >> run_app.py
echo         'postgres': { >> run_app.py
echo             'host': '', 'port': 5432, 'database': '', 'user': '', 'password': '', 'sslmode': 'require', 'database_url': '' >> run_app.py
echo         }, >> run_app.py
echo         'app': {'auto_backup': False, 'read_only_mode': False}, >> run_app.py
echo         'ui': {'theme': 'light', 'font_size': 10} >> run_app.py
echo     } >> run_app.py
echo     with open(cfg_path, 'w') as f: json.dump(template, f, indent=4) >> run_app.py
echo     print('Created Postgres config template at config.json - please fill credentials.') >> run_app.py
echo else: >> run_app.py
echo     print('Using existing config.json') >> run_app.py
echo try: >> run_app.py
echo     print('Starting ePetCare Vet Portal...') >> run_app.py
echo     with open('main.py','r',encoding='utf-8') as f: code = compile(f.read(),'main.py','exec'); exec(code) >> run_app.py
echo except Exception as e: >> run_app.py
echo     print('\nERROR:', e) >> run_app.py
echo     traceback.print_exc() >> run_app.py
echo     input('\nPress Enter to exit...') >> run_app.py

echo Script created (non-destructive).
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
