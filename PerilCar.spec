# PyInstaller spec — PerilCar ERP Desktop
# Build: pyinstaller PerilCar.spec --clean --noconfirm
# Output: dist/PerilCar/PerilCar.exe

block_cipher = None

a = Analysis(
    ['app_desktop.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('web', 'web'),
        ('core', 'core'),
        ('modules', 'modules'),
    ],
    hiddenimports=[
        'flask', 'flask_socketio', 'engineio.async_drivers.threading',
        'webview', 'webview.platforms.edgechromium', 'webview.platforms.winforms',
        'PIL', 'openpyxl', 'xlsxwriter', 'sqlite3', 'hashlib',
        'dev_server', 'core.config', 'core.database',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter.test', 'unittest', 'pytest', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PerilCar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                # NESSUN TERMINALE
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PerilCar',
)
