# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/app-icon.png',  # Use the app icon
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
