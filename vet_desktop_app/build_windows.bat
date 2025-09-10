@echo off
REM Build script for ePetCare Vet Desktop Application for Windows

echo Creating placeholder icons...
if not exist resources mkdir resources

REM Create placeholder icons if they don't exist
if not exist resources\app-icon.png (
    echo Creating placeholder app icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (64, 64), color=(0, 102, 204)); draw = ImageDraw.Draw(img); draw.rectangle([10, 10, 54, 54], fill=(255, 255, 255)); img.save('resources/app-icon.png')"
)

if not exist resources\refresh-icon.png (
    echo Creating placeholder refresh icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(0, 102, 204)); img.save('resources/refresh-icon.png')"
)

if not exist resources\appointment-icon.png (
    echo Creating placeholder appointment icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(0, 153, 51)); img.save('resources/appointment-icon.png')"
)

if not exist resources\search-icon.png (
    echo Creating placeholder search icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(153, 102, 0)); img.save('resources/search-icon.png')"
)

if not exist resources\calendar-icon.png (
    echo Creating placeholder calendar icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(153, 0, 153)); img.save('resources/calendar-icon.png')"
)

if not exist resources\dashboard-icon.png (
    echo Creating placeholder dashboard icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(0, 51, 102)); img.save('resources/dashboard-icon.png')"
)

if not exist resources\patients-icon.png (
    echo Creating placeholder patients icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(102, 51, 0)); img.save('resources/patients-icon.png')"
)

if not exist resources\appointments-icon.png (
    echo Creating placeholder appointments icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(0, 102, 51)); img.save('resources/appointments-icon.png')"
)

if not exist resources\settings-icon.png (
    echo Creating placeholder settings icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(51, 51, 51)); img.save('resources/settings-icon.png')"
)

if not exist resources\logout-icon.png (
    echo Creating placeholder logout icon...
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(153, 0, 0)); img.save('resources/logout-icon.png')"
)

REM Create app-icon.ico for Windows
if not exist resources\app-icon.ico (
    echo Converting app icon to ICO format...
    python -c "from PIL import Image; img = Image.open('resources/app-icon.png'); img.save('resources/app-icon.ico')"
)

echo Installing required packages...
pip install pyinstaller pillow

echo Building executable with PyInstaller...
pyinstaller epetcare_vet_desktop.spec

echo Building installer with NSIS...
REM Check if NSIS is installed and in PATH
where makensis > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo NSIS not found in PATH. Please install NSIS and add it to your PATH.
    echo You can download NSIS from https://nsis.sourceforge.io/Download
    echo After installation, run 'makensis installer.nsi' to create the installer.
) else (
    makensis installer.nsi
    echo Installer created: ePetCare_Vet_Desktop_Setup.exe
)

echo Done!
