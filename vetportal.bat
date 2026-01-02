@echo off
echo ========================================
echo ePetCare Vet Portal - Superadmin Dashboard
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
echo Installing/checking dependencies...
pip install PySide6 Pillow requests urllib3 certifi psycopg2-binary --quiet
echo Dependencies ready!
echo.

REM Check application configuration
echo Checking application configuration...
set "_CHECKCFG=check_config_tmp.py"
> "%_CHECKCFG%" echo import json, sys, io, os
>> "%_CHECKCFG%" echo p = os.path.join('vet_desktop_app','config.json')
>> "%_CHECKCFG%" echo if not os.path.exists(p):
>> "%_CHECKCFG%" echo ^	print('No config file found.')
>> "%_CHECKCFG%" echo ^	sys.exit(0)
>> "%_CHECKCFG%" echo try:
>> "%_CHECKCFG%" echo ^	with io.open(p,'r',encoding='utf-8') as f:
>> "%_CHECKCFG%" echo ^		data = json.load(f)
>> "%_CHECKCFG%" echo ^	server = data.get('app',{}).get('server_url','<missing>')
>> "%_CHECKCFG%" echo ^	pg = data.get('postgres',{})
>> "%_CHECKCFG%" echo ^	ok = bool(pg.get('database_url') or (pg.get('host') and pg.get('database') and pg.get('user')))
>> "%_CHECKCFG%" echo ^	print('server_url:', server)
>> "%_CHECKCFG%" echo ^	print('postgres config:', 'OK' if ok else 'MISSING')
>> "%_CHECKCFG%" echo except Exception as e:
>> "%_CHECKCFG%" echo ^	print('WARN: could not read config.json:', e)
>> "%_CHECKCFG%" echo ^	sys.exit(0)

python "%_CHECKCFG%"
del "%_CHECKCFG%" >nul 2>&1
echo.

REM Run the desktop app directly
echo Starting ePetCare Vet Portal...
echo.
cd vet_desktop_app
python main.py

REM Check if the application ran successfully
if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start properly
    echo Error code: %errorlevel%
    echo.
    cd ..
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
    cd ..
)

echo.
echo ========================================
echo Application finished
echo ========================================
pause
