# ePetCare Vet Desktop Application

A standalone desktop application for veterinarians to access the ePetCare system. This application connects to the same database as the ePetCare web application, allowing veterinarians to manage appointments, patients, and medical records from their desktop.

## Features

- **Patient Management**: View and manage pet and owner information
- **Appointment Scheduling**: Schedule, view, and manage appointments
- **Medical Records**: Access and update medical records, prescriptions, and treatments
- **Offline Mode**: Work offline and sync changes when back online
- **Database Integration**: Connects to the same SQLite database as the ePetCare web application

## Installation

### Prerequisites

- **Windows 10/11** or **Linux** operating system
- **Python 3.8** or higher (compatible with Python 3.13)
- **PySide6** (installed automatically by the installer)
- **Access to the ePetCare database** (SQLite file)

### Install from Binary (Recommended for Windows Users)

1. Download the latest `ePetCare_Vet_Desktop_Setup.exe` installer
2. Run the installer and follow the instructions
3. During installation, the installer will:
   - Create program files in the selected installation directory
   - Create a desktop shortcut and start menu entry
   - Configure the application to find the database
4. Launch the application from the desktop shortcut or start menu

### Install from Source (For Developers)

1. Clone the repository or download the source code
2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Make sure you have access to the ePetCare database file (db.sqlite3)
4. Update the `config.json` file with the correct path to your database:

```json
{
    "database": {
        "path": "C:\\path\\to\\your\\db.sqlite3",
        "backup_dir": "C:\\path\\to\\backups"
    }
}
```

5. Run the application:

```bash
python main.py
```

### Troubleshooting Installation Issues

#### Module Import Errors

If you see an error like `No module named 'views'` or similar:

1. **Use the launcher script**: Run `launcher.bat` which properly sets up the Python path
2. **Run the diagnostic script**: Execute `python debug.py` to identify import issues
3. **Check your Python path**: Make sure the application directory is in your Python path
4. **Reinstall the application**: The installer should set up everything correctly

#### Database Connection Issues

If you encounter database connection errors:

1. Make sure the database file exists at the specified path in `config.json`
2. If the path is incorrect, you can manually edit `config.json` in the installation directory
3. The application will also search for the database in common locations:
   - In the same directory as the application
   - In the parent directory
   - In the `data` subdirectory
4. Run `python debug.py` to check database connectivity

#### Windows-Specific Issues

1. **Missing DLLs**: If you get missing DLL errors, install the Visual C++ Redistributable:
   - Download from [Microsoft's website](https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads)

2. **Permission Issues**: If you get permission errors:
   - Right-click the application and select "Run as administrator"
   - Check that your user account has read/write access to the application directory

3. **Firewall Blocking**: If the application can't connect to the network:
   - Check your firewall settings
   - The installer should have added a firewall rule automatically

#### Running from Source Code

If you're running the application from source code:

1. Use one of the provided scripts:
   - `launcher.bat` - Smart launcher that tries executable first, then Python
   - `run.bat` - Sets up a virtual environment and runs the application
   - `run_direct.bat` - Runs directly with the system Python

2. If running manually with Python:
   ```bash
   # Set Python path to include current directory
   set PYTHONPATH=.;%PYTHONPATH%  # Windows
   export PYTHONPATH=.:$PYTHONPATH  # Linux/Mac
   
   # Run the application
   python main.py
   ```

3. If you still encounter module import issues:
   ```python
   # Add this to the top of main.py if not already there
   import sys, os
   sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
   ```

## Configuration

The application can be configured through the Settings menu. Key settings include:

- **Database Path**: Path to the SQLite database file
- **Backup Directory**: Directory to store database backups
- **Offline Mode**: Enable/disable offline mode
- **Sync Interval**: How often to sync changes when in offline mode
- **UI Theme**: Light or dark theme

## Building the Installer

### Windows

To build the installer on Windows, use the provided build script:

```bash
build_windows.bat
```

This script will:
1. Install required dependencies (PyInstaller, Pillow)
2. Create necessary resource files
3. Build the executable with PyInstaller
4. Create an installer with NSIS (if installed)

### Manual Build Process

If you prefer to build manually:

1. Install the required build tools:

```bash
pip install pyinstaller pillow
```

2. Make sure all resource files are in place (icons, stylesheet)

3. Build with PyInstaller:

```bash
pyinstaller epetcare_vet_desktop.spec
```

4. If you have NSIS installed, create the installer:

```bash
makensis installer.nsi
```

This will create a `dist` directory containing the bundled application and an installer executable `ePetCare_Vet_Desktop_Setup.exe`.

## License

This software is proprietary and confidential. Unauthorized copying, transferring, or reproduction of the contents of this software, via any medium, is strictly prohibited.

## Support

For support, please contact the ePetCare support team at support@epetcare.local.
