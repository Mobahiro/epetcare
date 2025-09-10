# ePetCare Vet Desktop - Windows Installer Guide

This guide explains how to build the Windows installer for the ePetCare Vet Desktop application.

## Prerequisites

### For Building on Windows

1. **Python 3.8 or higher** - Download from [python.org](https://www.python.org/downloads/)
2. **NSIS (Nullsoft Scriptable Install System)** - Download from [nsis.sourceforge.io](https://nsis.sourceforge.io/Download)
3. **Required Python packages**:
   - PySide6
   - PyInstaller
   - Pillow

### For Building on Linux/WSL

1. **Python 3.8 or higher**
2. **NSIS** - Install via package manager:
   - Ubuntu/Debian: `sudo apt-get install nsis`
   - Fedora: `sudo dnf install mingw64-nsis`
3. **Required Python packages**:
   - PySide6
   - PyInstaller
   - Pillow

## Building the Installer

### On Windows

1. Open Command Prompt or PowerShell
2. Navigate to the vet_desktop_app directory
3. Run the build script:
   ```
   build_windows.bat
   ```

### On Linux/WSL

1. Open a terminal
2. Navigate to the vet_desktop_app directory
3. Run the build script:
   ```
   ./build_windows.sh
   ```

## What the Build Scripts Do

1. Create placeholder icons in the resources directory
2. Install required Python packages
3. Build the executable with PyInstaller
4. Create the installer with NSIS

## Output Files

- **dist/ePetCare_Vet_Desktop/** - Directory containing the executable and all required files
- **ePetCare_Vet_Desktop_Setup.exe** - The Windows installer

## Installation

1. Run the installer: `ePetCare_Vet_Desktop_Setup.exe`
2. Follow the installation wizard
3. The application will be installed to the default location: `C:\Program Files\ePetCare\ePetCare Vet Desktop`
4. Shortcuts will be created on the desktop and in the Start Menu

## Troubleshooting

### Missing Icons

If you see "No Icon set" warnings, make sure the icons exist in the resources directory. The build scripts should create placeholder icons automatically.

### Database Connection Issues

By default, the installer will copy the database file (db.sqlite3) from the build directory to the installation directory. Make sure the database file exists before building the installer.

If you need to use a different database location, you can modify the config.json file after installation.

### NSIS Not Found

If you get an error about NSIS not being found, make sure NSIS is installed and added to your PATH. After installing NSIS, you can run `makensis installer.nsi` manually to create the installer.

## Customizing the Installer

You can customize the installer by editing the following files:

- **installer.nsi** - The NSIS script for creating the installer
- **LICENSE.txt** - The license agreement shown during installation
- **resources/app-icon.png** - The application icon
