@echo off
REM ePetCare Vet Portal Launcher
REM This script launches the Vet Desktop Application

REM Change to the script directory
cd /d "%~dp0"

REM Install required packages
echo Installing required packages...
pip install PySide6>=6.5.0 Pillow>=9.0.0

REM Create a temporary Python script to run the application
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
echo     with open('main.py') as f: >> run_app.py
echo         code = compile(f.read(), 'main.py', 'exec') >> run_app.py
echo         exec(code) >> run_app.py
echo except Exception as e: >> run_app.py
echo     print(f"\nERROR: {e}") >> run_app.py
echo     traceback.print_exc() >> run_app.py
echo     input("\nPress Enter to exit...") >> run_app.py

REM Run the Python script
echo Starting ePetCare Vet Portal...
python run_app.py

REM Clean up
del run_app.py

pause