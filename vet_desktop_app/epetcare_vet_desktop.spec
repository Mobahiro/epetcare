# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Add the current directory to the path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath('__file__')))

# Collect all submodules automatically
views_submodules = collect_submodules('views')
utils_submodules = collect_submodules('utils')
models_submodules = collect_submodules('models')

# Ensure these specific modules are included
critical_modules = [
    'models.data_access',
    'models.models',
    'views.main_window',
    'views.login_dialog',
    'utils.database',
    'utils.config'
]

# Collect all PySide6 modules
pyside6_submodules = ['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 
                      'PySide6.QtSvg', 'PySide6.QtNetwork', 'PySide6.QtSql',
                      'PySide6.support']

a = Analysis(
    ['main.py'],
    pathex=[os.path.dirname(os.path.abspath('__file__'))],
    binaries=[],
    datas=[
        ('views', 'views'),
        ('utils', 'utils'),
        ('models', 'models'),
        ('controllers', 'controllers'),
        ('resources', 'resources'),
        ('config.json', '.'),
        ('data', 'data'),
        ('data/db.sqlite3', 'data'),  # Explicitly include the database file
    ],
    hiddenimports=[
        # PySide6 modules
        *pyside6_submodules,
        # Application modules
        *views_submodules,
        *utils_submodules,
        *models_submodules,
        # Critical modules that must be included
        *critical_modules,
        # Explicitly include these modules
        'sqlite3',
        'json',
        'datetime',
        'pathlib',
        'shutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hook-runtime.py', 'module_finder.py', 'package_init.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add resources and data files
a.datas += [
    ('config.json', 'config.json', 'DATA'),
    ('resources/app-icon.png', 'resources/app-icon.png', 'DATA'),
    ('resources/refresh-icon.png', 'resources/refresh-icon.png', 'DATA'),
    ('resources/appointment-icon.png', 'resources/appointment-icon.png', 'DATA'),
    ('resources/search-icon.png', 'resources/search-icon.png', 'DATA'),
    ('resources/calendar-icon.png', 'resources/calendar-icon.png', 'DATA'),
    ('resources/dashboard-icon.png', 'resources/dashboard-icon.png', 'DATA'),
    ('resources/patients-icon.png', 'resources/patients-icon.png', 'DATA'),
    ('resources/appointments-icon.png', 'resources/appointments-icon.png', 'DATA'),
    ('resources/settings-icon.png', 'resources/settings-icon.png', 'DATA'),
    ('resources/logout-icon.png', 'resources/logout-icon.png', 'DATA'),
    ('resources/style.qss', 'resources/style.qss', 'DATA'),
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ePetCare_Vet_Desktop',  # No spaces for Windows compatibility
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Set to True for debugging, change to False for production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/app-icon.ico',  # Use the ico file instead of png
    version='file_version_info.txt',  # Add version info
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ePetCare_Vet_Desktop',  # No spaces for Windows compatibility
)
