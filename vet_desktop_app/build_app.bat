@echo off
REM Build script for ePetCare Vet Desktop Application
setlocal enabledelayedexpansion

echo ===== ePetCare Vet Desktop Application Builder =====

REM Change to the script directory
cd /d "%~dp0"

REM Check if Python is installed
where python > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt
pip install pyinstaller pillow

REM Create resources directory if it doesn't exist
if not exist resources mkdir resources

REM Create style.qss if it doesn't exist
if not exist resources\style.qss (
    echo Creating placeholder style.qss...
    echo /* ePetCare Vet Desktop Application Stylesheet */ > resources\style.qss
    echo QWidget { font-family: 'Segoe UI'; font-size: 10pt; } >> resources\style.qss
    echo QMainWindow { background-color: #f0f0f0; } >> resources\style.qss
    echo QPushButton { background-color: #0066cc; color: white; padding: 5px 10px; border-radius: 3px; } >> resources\style.qss
    echo QPushButton:hover { background-color: #0055aa; } >> resources\style.qss
)

REM Create placeholder icons if they don't exist
if not exist resources\app-icon.png (
    echo Creating placeholder app icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (64, 64), color=(0, 102, 204)); draw = ImageDraw.Draw(img); draw.rectangle([10, 10, 54, 54], fill=(255, 255, 255)); img.save('resources/app-icon.png')"
)

REM Create app-icon.ico for Windows
if not exist resources\app-icon.ico (
    echo Converting app icon to ICO format...
    python -c "from PIL import Image; img = Image.open('resources/app-icon.png'); img.save('resources/app-icon.ico')"
)

REM Create data directory if it doesn't exist
if not exist data mkdir data

REM Try to find the database file in various locations
echo Searching for database file...
set DB_FOUND=0
set DB_PATH=

REM Check in parent directory
if exist ..\db.sqlite3 (
    echo Found database in parent directory.
    set DB_FOUND=1
    set DB_PATH=..\db.sqlite3
)

REM Check in current directory
if %DB_FOUND%==0 (
    if exist db.sqlite3 (
        echo Found database in current directory.
        set DB_FOUND=1
        set DB_PATH=db.sqlite3
    )
)

REM Check in root directory
if %DB_FOUND%==0 (
    if exist C:\Users\Shiro\epetcare\db.sqlite3 (
        echo Found database in root directory.
        set DB_FOUND=1
        set DB_PATH=C:\Users\Shiro\epetcare\db.sqlite3
    )
)

REM Copy the database if found
if %DB_FOUND%==1 (
    echo Copying database file from %DB_PATH%...
    copy /Y "%DB_PATH%" data\db.sqlite3 > nul
    echo Database copied successfully.
) else (
    echo WARNING: Database file not found in any common location.
    echo Please make sure the database file exists and is accessible.
    echo Creating a placeholder database file...
    
    REM Create a minimal SQLite database with the required tables
    echo Creating minimal SQLite database...
    python -c "import sqlite3; conn = sqlite3.connect('data/db.sqlite3'); c = conn.cursor(); c.execute('CREATE TABLE IF NOT EXISTS auth_user (id INTEGER PRIMARY KEY, username TEXT, password TEXT, first_name TEXT, last_name TEXT, email TEXT, is_active INTEGER, date_joined TEXT, last_login TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS clinic_owner (id INTEGER PRIMARY KEY, full_name TEXT, email TEXT, phone TEXT, address TEXT, created_at TEXT, user_id INTEGER)'); c.execute('CREATE TABLE IF NOT EXISTS clinic_pet (id INTEGER PRIMARY KEY, owner_id INTEGER, name TEXT, species TEXT, breed TEXT, sex TEXT, birth_date TEXT, weight_kg REAL, notes TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS clinic_appointment (id INTEGER PRIMARY KEY, pet_id INTEGER, date_time TEXT, reason TEXT, notes TEXT, status TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS clinic_medicalrecord (id INTEGER PRIMARY KEY, pet_id INTEGER, visit_date TEXT, condition TEXT, treatment TEXT, vet_notes TEXT)'); c.execute('CREATE TABLE IF NOT EXISTS clinic_prescription (id INTEGER PRIMARY KEY, pet_id INTEGER, medication_name TEXT, dosage TEXT, instructions TEXT, date_prescribed TEXT, duration_days INTEGER, is_active INTEGER)'); c.execute('CREATE TABLE IF NOT EXISTS vet_veterinarian (id INTEGER PRIMARY KEY, user_id INTEGER, full_name TEXT, specialization TEXT, license_number TEXT, phone TEXT, bio TEXT, created_at TEXT)'); conn.commit(); conn.close(); print('Created minimal database with required tables')"
    
    REM Insert a test user
    echo Inserting test user...
    python -c "import sqlite3; conn = sqlite3.connect('data/db.sqlite3'); c = conn.cursor(); c.execute('INSERT INTO auth_user (username, password, first_name, last_name, email, is_active, date_joined, last_login) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', ('admin', 'admin', 'Admin', 'User', 'admin@example.com', 1, '2023-01-01T00:00:00', '2023-01-01T00:00:00')); c.execute('INSERT INTO vet_veterinarian (user_id, full_name, specialization, license_number, phone, bio, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)', (1, 'Admin User', 'General', 'VET123', '555-1234', 'Test veterinarian', '2023-01-01T00:00:00')); conn.commit(); conn.close(); print('Inserted test user and veterinarian')"
)

REM Update config.json to use the local database path
echo Updating config.json...
python -c "import json, os; config = json.load(open('config.json')) if os.path.exists('config.json') else {}; config.setdefault('database', {}); config['database']['path'] = os.path.normpath(os.path.join('.', 'data', 'db.sqlite3')); config['database']['backup_dir'] = os.path.normpath(os.path.join('.', 'backups')); json.dump(config, open('config.json', 'w'), indent=4)"

REM Clean previous build files
echo Cleaning previous build files...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist
if exist __pycache__ rmdir /S /Q __pycache__

REM Make sure all required scripts are included in the PyInstaller spec
echo Checking required scripts are included in the spec...

REM Check for module_finder.py
python -c "import re; spec = open('epetcare_vet_desktop.spec', 'r').read(); module_finder_found = 'module_finder.py' in spec; print(f'module_finder.py found in spec: {module_finder_found}'); exit(0 if module_finder_found else 1)" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Adding module_finder.py to the PyInstaller spec...
    python -c "spec = open('epetcare_vet_desktop.spec', 'r').read(); spec = spec.replace(\"'hook-runtime.py'\", \"'hook-runtime.py', 'module_finder.py'\"); open('epetcare_vet_desktop.spec', 'w').write(spec)"
)

REM Check for package_init.py
python -c "import re; spec = open('epetcare_vet_desktop.spec', 'r').read(); package_init_found = 'package_init.py' in spec; print(f'package_init.py found in spec: {package_init_found}'); exit(0 if package_init_found else 1)" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Adding package_init.py to the PyInstaller spec...
    python -c "spec = open('epetcare_vet_desktop.spec', 'r').read(); if 'module_finder.py' in spec: spec = spec.replace(\"'module_finder.py'\", \"'module_finder.py', 'package_init.py'\"); else: spec = spec.replace(\"'hook-runtime.py'\", \"'hook-runtime.py', 'package_init.py'\"); open('epetcare_vet_desktop.spec', 'w').write(spec)"
)

REM Build executable with PyInstaller
echo Building executable with PyInstaller...
pyinstaller --clean epetcare_vet_desktop.spec

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller build failed.
    echo Please check the error messages above.
    pause
    exit /b 1
)

REM Verify the executable was created
if not exist dist\ePetCare_Vet_Desktop\ePetCare_Vet_Desktop.exe (
    echo ERROR: Executable was not created.
    pause
    exit /b 1
)

echo ===== Build completed successfully! =====
echo.
echo The executable can be found at:
echo %CD%\dist\ePetCare_Vet_Desktop\ePetCare_Vet_Desktop.exe
echo.
echo You can run it directly or use the run_debug.bat script for debugging.
echo.

pause
