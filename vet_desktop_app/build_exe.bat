@echo off
REM Specialized build script for creating the ePetCare Vet Desktop executable
setlocal enabledelayedexpansion

echo ===== ePetCare Vet Desktop - EXE Builder =====

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

REM Check Python version
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python 3.8 or higher is required.
    echo Current Python version:
    python --version
    pause
    exit /b 1
)

REM Install required packages
echo Installing required packages...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller==6.15.0 pillow

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

REM Copy database if it exists in the parent directory
if exist ..\db.sqlite3 (
    echo Copying database file...
    copy /Y ..\db.sqlite3 data\db.sqlite3 > nul
    echo Database copied successfully.
) else (
    echo WARNING: Database file not found in parent directory.
    echo Creating an empty data directory...
    if not exist data\db.sqlite3 (
        echo. > data\db.sqlite3
    )
)

REM Update config.json to use the local database path
echo Updating config.json...
python -c "import json, os; config = json.load(open('config.json')) if os.path.exists('config.json') else {}; config.setdefault('database', {}); config['database']['path'] = os.path.normpath(os.path.join('.', 'data', 'db.sqlite3')); config['database']['backup_dir'] = os.path.normpath(os.path.join('.', 'backups')); json.dump(config, open('config.json', 'w'), indent=4)"

REM Create backups directory if it doesn't exist
if not exist backups mkdir backups

REM Clean previous build files
echo Cleaning previous build files...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist
if exist __pycache__ rmdir /S /Q __pycache__

REM Set PYTHONPATH to include the current directory
set PYTHONPATH=%CD%;%PYTHONPATH%

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

REM Copy additional files to the dist directory
echo Copying additional files to dist directory...

REM Copy database if not already included
if not exist dist\ePetCare_Vet_Desktop\data mkdir dist\ePetCare_Vet_Desktop\data
if exist data\db.sqlite3 (
    copy /Y data\db.sqlite3 dist\ePetCare_Vet_Desktop\data\db.sqlite3 > nul
)

REM Copy config.json if not already included
copy /Y config.json dist\ePetCare_Vet_Desktop\config.json > nul

REM Create a launcher for the executable
echo Creating launcher...
echo @echo off > dist\ePetCare_Vet_Desktop\run_app.bat
echo start "" "ePetCare_Vet_Desktop.exe" >> dist\ePetCare_Vet_Desktop\run_app.bat

echo ===== Build completed successfully! =====
echo.
echo The executable can be found at:
echo %CD%\dist\ePetCare_Vet_Desktop\ePetCare_Vet_Desktop.exe
echo.
echo You can run it directly or use the run_app.bat launcher.
echo.

REM Ask if user wants to run the application
set /p run_app="Do you want to run the application now? (Y/N): "
if /i "%run_app%"=="Y" (
    echo Starting application...
    start "" "dist\ePetCare_Vet_Desktop\ePetCare_Vet_Desktop.exe"
)

pause
