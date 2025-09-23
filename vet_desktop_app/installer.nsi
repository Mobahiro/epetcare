; ePetCare Vet Desktop Installer Script
; NSIS (Nullsoft Scriptable Install System) script

; Define constants
!define APPNAME "ePetCare Vet Desktop"
!define COMPANYNAME "ePetCare"
!define DESCRIPTION "Veterinarian Desktop Application for ePetCare"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://www.epetcare.local/help"
!define UPDATEURL "https://www.epetcare.local/update"
!define ABOUTURL "https://www.epetcare.local/about"

; Main Install settings
Name "${APPNAME}"
InstallDir "$PROGRAMFILES\${COMPANYNAME}\${APPNAME}"
InstallDirRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}" "Install_Dir"
RequestExecutionLevel admin
Icon "resources\app-icon.ico"
OutFile "ePetCare_Vet_Desktop_Setup.exe"

; Modern interface settings
!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "resources\app-icon.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Set languages (first is default language)
!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath $INSTDIR
    
    ; Copy all files from the PyInstaller dist directory
    File /r "dist\ePetCare_Vet_Desktop\*.*"
    
    ; Create database directory
    CreateDirectory "$INSTDIR\data"
    
    ; Copy database if it exists
    IfFileExists "db.sqlite3" 0 +2
    File /oname=data\db.sqlite3 "db.sqlite3"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    ; Create start menu shortcut
    CreateDirectory "$SMPROGRAMS\${COMPANYNAME}"
    CreateShortCut "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk" "$INSTDIR\ePetCare_Vet_Desktop.exe" "" "$INSTDIR\ePetCare_Vet_Desktop.exe" 0
    
    ; Create desktop shortcut
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\ePetCare_Vet_Desktop.exe" "" "$INSTDIR\ePetCare_Vet_Desktop.exe" 0
    
    ; Write registry information for add/remove programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayIcon" "$\"$INSTDIR\ePetCare_Vet_Desktop.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "HelpLink" "$\"${HELPURL}$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLUpdateInfo" "$\"${UPDATEURL}$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "URLInfoAbout" "$\"${ABOUTURL}$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    
    ; Register application in Windows Firewall
    ExecWait 'netsh advfirewall firewall add rule name="${APPNAME}" dir=in action=allow program="$INSTDIR\ePetCare_Vet_Desktop.exe" enable=yes profile=private,domain description="Allow ${APPNAME} to access the network"'
    
    ; Create config.json if it doesn't exist
    IfFileExists "$INSTDIR\config.json" +2 0
    FileOpen $0 "$INSTDIR\config.json" w
    FileWrite $0 '{"database": {"path": "$INSTDIR\\data\\db.sqlite3", "backup_dir": "$INSTDIR\\backups"}, "app": {"offline_mode": false, "sync_interval": 300, "auto_backup": true}, "ui": {"theme": "light", "font_size": 10}}'
    FileClose $0
    
    ; Create backups directory
    CreateDirectory "$INSTDIR\backups"
SectionEnd

Section "Uninstall"
    ; Remove Start Menu shortcuts
    Delete "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk"
    RMDir "$SMPROGRAMS\${COMPANYNAME}"
    
    ; Remove Desktop shortcut
    Delete "$DESKTOP\${APPNAME}.lnk"
    
    ; Remove Firewall rule
    ExecWait 'netsh advfirewall firewall delete rule name="${APPNAME}"'
    
    ; Remove registry keys
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${COMPANYNAME} ${APPNAME}"
    DeleteRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}"
    
    ; Remove files and directories
    RMDir /r "$INSTDIR"
SectionEnd
