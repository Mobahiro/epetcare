#!/bin/bash
# Build script for ePetCare Vet Desktop Application for Windows (Linux/WSL version)

echo "Creating placeholder icons..."
mkdir -p resources

# Create placeholder icons if they don't exist
if [ ! -f resources/app-icon.png ]; then
    echo "Creating placeholder app icon..."
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (64, 64), color=(0, 102, 204)); draw = ImageDraw.Draw(img); draw.rectangle([10, 10, 54, 54], fill=(255, 255, 255)); img.save('resources/app-icon.png')"
fi

if [ ! -f resources/refresh-icon.png ]; then
    echo "Creating placeholder refresh icon..."
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(0, 102, 204)); img.save('resources/refresh-icon.png')"
fi

if [ ! -f resources/appointment-icon.png ]; then
    echo "Creating placeholder appointment icon..."
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(0, 153, 51)); img.save('resources/appointment-icon.png')"
fi

if [ ! -f resources/search-icon.png ]; then
    echo "Creating placeholder search icon..."
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(153, 102, 0)); img.save('resources/search-icon.png')"
fi

if [ ! -f resources/calendar-icon.png ]; then
    echo "Creating placeholder calendar icon..."
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(153, 0, 153)); img.save('resources/calendar-icon.png')"
fi

if [ ! -f resources/dashboard-icon.png ]; then
    echo "Creating placeholder dashboard icon..."
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(0, 51, 102)); img.save('resources/dashboard-icon.png')"
fi

if [ ! -f resources/patients-icon.png ]; then
    echo "Creating placeholder patients icon..."
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(102, 51, 0)); img.save('resources/patients-icon.png')"
fi

if [ ! -f resources/appointments-icon.png ]; then
    echo "Creating placeholder appointments icon..."
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(0, 102, 51)); img.save('resources/appointments-icon.png')"
fi

if [ ! -f resources/settings-icon.png ]; then
    echo "Creating placeholder settings icon..."
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(51, 51, 51)); img.save('resources/settings-icon.png')"
fi

if [ ! -f resources/logout-icon.png ]; then
    echo "Creating placeholder logout icon..."
    python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (32, 32), color=(153, 0, 0)); img.save('resources/logout-icon.png')"
fi

# Create app-icon.ico for Windows
if [ ! -f resources/app-icon.ico ]; then
    echo "Converting app icon to ICO format..."
    python -c "from PIL import Image; img = Image.open('resources/app-icon.png'); img.save('resources/app-icon.ico')"
fi

echo "Installing required packages..."
pip install pyinstaller pillow

echo "Building executable with PyInstaller..."
pyinstaller epetcare_vet_desktop.spec

echo "Building installer with NSIS..."
# Check if NSIS is installed
if command -v makensis &> /dev/null; then
    makensis installer.nsi
    echo "Installer created: ePetCare_Vet_Desktop_Setup.exe"
else
    echo "NSIS not found. Please install NSIS to create the installer."
    echo "On Ubuntu/Debian: sudo apt-get install nsis"
    echo "On Fedora: sudo dnf install mingw64-nsis"
    echo "After installation, run 'makensis installer.nsi' to create the installer."
fi

echo "Done!"
