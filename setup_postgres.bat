@echo off
echo ===== ePetCare PostgreSQL Configuration Tool =====
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
    pause
    exit /b 1
)

REM Install required dependencies
echo Installing PostgreSQL driver...
pip install psycopg2-binary requests
echo.

REM Create a Python script to update the configuration
echo import json, os, sys > update_config.py
echo def update_postgres_config(): >> update_config.py
echo     """Update the PostgreSQL configuration""" >> update_config.py
echo     config_path = os.path.join('vet_desktop_app', 'config.json') >> update_config.py
echo     if not os.path.exists(config_path): >> update_config.py
echo         print("Config file not found at", config_path) >> update_config.py
echo         return False >> update_config.py
echo     try: >> update_config.py
echo         # Load existing config >> update_config.py
echo         with open(config_path, 'r') as f: >> update_config.py
echo             config = json.load(f) >> update_config.py
echo         # Get PostgreSQL settings from user >> update_config.py
echo         print("\nEnter PostgreSQL Database Settings:") >> update_config.py
echo         host = input("PostgreSQL Host (e.g., dpg-xxxx.oregon-postgres.render.com): ").strip() >> update_config.py
echo         port = input("PostgreSQL Port [5432]: ").strip() or 5432 >> update_config.py
echo         database = input("Database Name (e.g., epetcare): ").strip() >> update_config.py
echo         username = input("Database Username (e.g., epetcare): ").strip() >> update_config.py
echo         password = input("Database Password: ").strip() >> update_config.py
echo         # Create or update db_sync section >> update_config.py
echo         if 'db_sync' not in config: >> update_config.py
echo             config['db_sync'] = {} >> update_config.py
echo         # Update PostgreSQL configuration >> update_config.py
echo         config['db_sync']['postgres'] = { >> update_config.py
echo             "enabled": True, >> update_config.py
echo             "host": host, >> update_config.py
echo             "port": int(port), >> update_config.py
echo             "database": database, >> update_config.py
echo             "username": username, >> update_config.py
echo             "password": password >> update_config.py
echo         } >> update_config.py
echo         # Add deploy hook if not present >> update_config.py
echo         if 'remote_database' not in config: >> update_config.py
echo             config['remote_database'] = {} >> update_config.py
echo         deploy_hook = config['remote_database'].get('deploy_hook') >> update_config.py
echo         if not deploy_hook: >> update_config.py
echo             deploy_hook = input("\nEnter Render Deploy Hook URL (optional): ").strip() >> update_config.py
echo             if deploy_hook: >> update_config.py
echo                 config['remote_database']['deploy_hook'] = deploy_hook >> update_config.py
echo         # Save updated config >> update_config.py
echo         with open(config_path, 'w') as f: >> update_config.py
echo             json.dump(config, f, indent=4) >> update_config.py
echo         print("\nConfiguration updated successfully!") >> update_config.py
echo         return True >> update_config.py
echo     except Exception as e: >> update_config.py
echo         print(f"Error updating configuration: {e}") >> update_config.py
echo         return False >> update_config.py
echo # Run the function >> update_config.py
echo update_postgres_config() >> update_config.py
echo input("\nPress Enter to continue...") >> update_config.py

REM Run the Python script
python update_config.py

REM Clean up
if exist update_config.py (
    del update_config.py >nul 2>&1
)

REM Run the test script if requested
echo.
set /p RUN_TEST="Do you want to test the PostgreSQL connection? (y/n): "
if /i "%RUN_TEST%" == "y" (
    echo.
    python test_postgres.py
)

echo.
echo Configuration completed. You can now start the Vet Portal application.
echo.
pause