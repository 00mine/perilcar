# PyInstaller spec — PerilCar ERP Desktop
block_cipher = None

a = Analysis(
    ['app_desktop.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('web', 'web'),
    ],
    hiddenimports=[
        'flask', 'flask_socketio',
        'engineio.async_drivers.threading',
        'PIL', 'PIL.Image', 'PIL.ImageDraw',
        'openpyxl', 'xlsxwriter',
        'sqlite3', 'hashlib',
        'dev_server',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'webview', 'pywebview', 'pythonnet',
        'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'unittest', 'pytest',
    ],
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
    console=False,
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
