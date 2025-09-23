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

### For End Users

1. Double-click the installer: `ePetCare_Vet_Desktop_Setup.exe`
2. If you see a Windows security warning, click "Run" or "Yes"
3. Follow the installation wizard:
   - Accept the license agreement
   - Choose the installation directory (default: `C:\Program Files\ePetCare\ePetCare Vet Desktop`)
   - Wait for the installation to complete
4. Shortcuts will be created on the desktop and in the Start Menu
5. Launch the application from the desktop shortcut

### First Launch Configuration

When you first launch the application:

1. If the database is not found automatically, you'll see a dialog asking for the database location
2. Navigate to where your `db.sqlite3` file is located (typically in the main ePetCare directory)
3. The application will remember this location for future use

### Running from Source Code

If you're installing from source code (not using the installer), you have several options:

1. **Launcher Script** (Recommended):
   - Double-click `launcher.bat` in the vet_desktop_app directory
   - This script will try to run the compiled executable first, and if not found, will run the Python script

2. **Virtual Environment**:
   - Double-click `run.bat` in the vet_desktop_app directory
   - This script creates a virtual environment, installs dependencies, and runs the application

3. **Direct Run**:
   - Double-click `run_direct.bat` in the vet_desktop_app directory
   - This script runs the application directly with the system Python without creating a virtual environment

4. **Debug Mode**:
   - Run `python debug.py` to diagnose common issues
   - This will check for missing modules, database connectivity, and resource files

### Silent Installation (For IT Administrators)

To perform a silent installation:

```
ePetCare_Vet_Desktop_Setup.exe /S
```

This will install the application without showing any dialogs, using all default settings.

## Troubleshooting

### Installation Issues

#### Windows Defender/Antivirus Blocking Installation
- The installer may be flagged by Windows Defender or other antivirus software
- This is a false positive due to the installer not being signed
- You can safely add an exception or click "More info" → "Run anyway" in the Windows SmartScreen dialog

#### Permission Issues
- If you get "Access denied" errors during installation:
  - Right-click the installer and select "Run as administrator"
  - Make sure you have administrator privileges on your computer

#### Installation Fails
- Make sure you have enough disk space
- Close any running instances of the application before installing
- Try running the installer in compatibility mode for Windows 10

### Application Issues

#### Module Import Errors ("No module named 'views'")
- This error occurs when Python can't find the application modules
- **Solutions**:
  1. Use the `launcher.bat` script which properly sets up the Python path
  2. Run the diagnostic script: `python debug.py` to identify import issues
  3. Set the PYTHONPATH environment variable: `set PYTHONPATH=C:\path\to\vet_desktop_app;%PYTHONPATH%`
  4. Reinstall the application using the installer

#### Database Connection Issues
- By default, the installer will copy the database file (db.sqlite3) from the build directory to the installation directory
- If the database is not found, the application will prompt you to locate it
- Common database locations:
  - `C:\Users\[username]\epetcare\db.sqlite3`
  - `C:\Program Files\ePetCare\ePetCare Vet Desktop\data\db.sqlite3`
  - The main ePetCare web application directory
- You can run `python debug.py` to check database connectivity

#### Missing Icons or UI Elements
- If icons or UI elements are missing:
  - Reinstall the application to restore missing files
  - Make sure you have the Visual C++ Redistributable installed
  - Try running the application as administrator

#### Application Crashes on Startup
- Check the Windows Event Viewer for error details
- Make sure all required DLLs are present in the installation directory
- Try reinstalling the application
- Run `python debug.py` to diagnose issues

### Running from Source

#### Python Path Issues
- If you get module import errors when running from source:
  - Use one of the provided scripts: `launcher.bat`, `run.bat`, or `run_direct.bat`
  - Set the PYTHONPATH environment variable: `set PYTHONPATH=.;%PYTHONPATH%`
  - Modify the main.py file to add the current directory to sys.path

#### PySide6 Installation Issues
- If you get errors about missing PySide6:
  - Install it manually: `pip install PySide6>=6.5.0`
  - Make sure you're using Python 3.8 or higher
  - Check for any error messages during installation

#### Running the Debug Script
- If you're having issues, run the debug script: `python debug.py`
- This will check:
  - Python version and environment
  - Required module imports
  - Database connectivity
  - Resource files existence
- The debug script will provide detailed information about any issues

### Build Issues

#### Missing Icons During Build
- If you see "No Icon set" warnings, make sure the icons exist in the resources directory
- The build scripts should create placeholder icons automatically

#### NSIS Not Found
- If you get an error about NSIS not being found, make sure NSIS is installed and added to your PATH
- After installing NSIS, you can run `makensis installer.nsi` manually to create the installer

#### PyInstaller Errors
- Make sure you have the latest version of PyInstaller installed
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Try running PyInstaller with the `--clean` flag to clear the cache
- Make sure the spec file includes all necessary modules and data files

## Customizing the Installer

You can customize the installer by editing the following files:

- **installer.nsi** - The NSIS script for creating the installer
- **LICENSE.txt** - The license agreement shown during installation
- **resources/app-icon.png** - The application icon
