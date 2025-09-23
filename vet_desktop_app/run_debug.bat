@echo off
REM Debug launcher for ePetCare Vet Desktop Application
REM This script runs the application in debug mode with additional logging

echo ===== ePetCare Vet Desktop - Debug Mode =====

REM Change to the script directory
cd /d "%~dp0"

REM Check if executable exists in dist directory
if exist dist\ePetCare_Vet_Desktop\ePetCare_Vet_Desktop.exe (
    echo Found executable, running in debug mode...
    
    REM Set debug environment variable
    set EPETCARE_DEBUG=1
    
    REM Create logs directory if it doesn't exist
    if not exist logs mkdir logs
    
    REM Run the executable and redirect output to log file
    echo Running executable with output redirected to logs\debug.log
    echo Timestamp: %date% %time% > logs\debug.log
    echo. >> logs\debug.log
    dist\ePetCare_Vet_Desktop\ePetCare_Vet_Desktop.exe >> logs\debug.log 2>&1
    
    echo.
    echo Application exited. Check logs\debug.log for details.
    
    REM Ask if user wants to view the log
    set /p view_log="Do you want to view the log file? (Y/N): "
    if /i "%view_log%"=="Y" (
        start "" notepad logs\debug.log
    )
) else if exist dist\ePetCare_Vet_Desktop.exe (
    echo Found executable in dist directory, running in debug mode...
    
    REM Set debug environment variable
    set EPETCARE_DEBUG=1
    
    REM Create logs directory if it doesn't exist
    if not exist logs mkdir logs
    
    REM Run the executable and redirect output to log file
    echo Running executable with output redirected to logs\debug.log
    echo Timestamp: %date% %time% > logs\debug.log
    echo. >> logs\debug.log
    dist\ePetCare_Vet_Desktop.exe >> logs\debug.log 2>&1
    
    echo.
    echo Application exited. Check logs\debug.log for details.
    
    REM Ask if user wants to view the log
    set /p view_log="Do you want to view the log file? (Y/N): "
    if /i "%view_log%"=="Y" (
        start "" notepad logs\debug.log
    )
) else (
    echo Executable not found. Building the application first...
    
    REM Run the build script
    call build_exe.bat
    
    REM Check if build was successful
    if exist dist\ePetCare_Vet_Desktop\ePetCare_Vet_Desktop.exe (
        echo Build successful, running in debug mode...
        
        REM Set debug environment variable
        set EPETCARE_DEBUG=1
        
        REM Create logs directory if it doesn't exist
        if not exist logs mkdir logs
        
        REM Run the executable and redirect output to log file
        echo Running executable with output redirected to logs\debug.log
        echo Timestamp: %date% %time% > logs\debug.log
        echo. >> logs\debug.log
        dist\ePetCare_Vet_Desktop\ePetCare_Vet_Desktop.exe >> logs\debug.log 2>&1
        
        echo.
        echo Application exited. Check logs\debug.log for details.
        
        REM Ask if user wants to view the log
        set /p view_log="Do you want to view the log file? (Y/N): "
        if /i "%view_log%"=="Y" (
            start "" notepad logs\debug.log
        )
    ) else (
        echo Build failed. Please check the error messages.
    )
)

pause
