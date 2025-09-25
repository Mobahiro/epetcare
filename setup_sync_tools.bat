@echo off
echo ===============================================================
echo  ePetCare Sync Tools - Setup
echo ===============================================================
echo.
echo This script will install all required dependencies for the
echo database synchronization tools.
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul

echo.
echo Step 1: Checking Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH.
    echo Please install Python and add it to your PATH.
    goto :error
)

echo.
echo Step 2: Installing required Python packages...
python -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Failed to upgrade pip. Continuing...
)

echo.
echo Installing requests, psutil, and other dependencies...
python -m pip install requests psutil Django dj-database-url psycopg2-binary
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Some packages might not have installed correctly.
    echo You may need to install them manually.
) else (
    echo All packages installed successfully!
)

echo.
echo Step 3: Checking database configuration...
if not exist "vet_desktop_app\config.json" (
    echo Warning: config.json not found!
    echo Please make sure your configuration file is properly set up.
) else (
    echo Configuration file found.
)

echo.
echo Step 4: Verifying sync tools...
echo Checking for diagnose_db_sync.py...
if not exist "diagnose_db_sync.py" (
    echo Warning: diagnose_db_sync.py not found!
)

echo Checking for monitor_db_sync.py...
if not exist "monitor_db_sync.py" (
    echo Warning: monitor_db_sync.py not found!
)

echo Checking for sync_dashboard.py...
if not exist "sync_dashboard.py" (
    echo Warning: sync_dashboard.py not found!
)

echo.
echo Step 5: Creating desktop shortcuts...
echo @echo off > "%TEMP%\create_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") >> "%TEMP%\create_shortcut.vbs"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\ePetCare Sync Dashboard.lnk" >> "%TEMP%\create_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_shortcut.vbs"
echo oLink.TargetPath = "cmd.exe" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Arguments = "/c cd /d %CD% && python sync_dashboard.py" >> "%TEMP%\create_shortcut.vbs"
echo oLink.WorkingDirectory = "%CD%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Description = "ePetCare Sync Dashboard" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Save >> "%TEMP%\create_shortcut.vbs"
cscript /nologo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"

echo @echo off > "%TEMP%\create_shortcut2.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") >> "%TEMP%\create_shortcut2.vbs"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\ePetCare Sync Tools.lnk" >> "%TEMP%\create_shortcut2.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_shortcut2.vbs"
echo oLink.TargetPath = "%CD%\sync_tools.bat" >> "%TEMP%\create_shortcut2.vbs"
echo oLink.WorkingDirectory = "%CD%" >> "%TEMP%\create_shortcut2.vbs"
echo oLink.Description = "ePetCare Sync Tools" >> "%TEMP%\create_shortcut2.vbs"
echo oLink.Save >> "%TEMP%\create_shortcut2.vbs"
cscript /nologo "%TEMP%\create_shortcut2.vbs"
del "%TEMP%\create_shortcut2.vbs"

echo.
echo ===============================================================
echo  Setup Complete!
echo ===============================================================
echo.
echo Shortcuts created on your desktop:
echo  - ePetCare Sync Dashboard
echo  - ePetCare Sync Tools
echo.
echo To start using the sync tools:
echo  1. Run the "ePetCare Sync Tools" shortcut
echo  2. Choose option 4 to open the dashboard
echo  3. Use the dashboard to monitor and manage database sync
echo.
goto :end

:error
echo.
echo ===============================================================
echo  Error: Setup could not be completed.
echo ===============================================================
echo.
echo Please see the error messages above for details on how to fix
echo the issues manually.
echo.

:end
echo Press any key to exit...
pause > nul