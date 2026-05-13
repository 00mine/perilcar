@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo.
echo  PerilCar ERP - Build App Desktop
echo  ========================================
echo.

REM ─── Cerca Python 3.12 o 3.11 (non 3.13+) ───────────────────────────
set PYTHON=
for %%v in (3.12 3.11 3.10) do (
    if "!PYTHON!"=="" (
        for %%p in (
            "C:\Python%%~v\python.exe"
            "C:\Program Files\Python%%~v\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python%%~v\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python%%~v-64\python.exe"
        ) do (
            if "!PYTHON!"=="" if exist %%p (
                set PYTHON=%%p
                echo [OK] Trovato Python in %%p
            )
        )
    )
)

REM Se non trovato, usa il Python di sistema e verifica versione
if "!PYTHON!"=="" (
    python --version >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
        REM Accetta 3.8 - 3.12
        echo !PYVER! | findstr /r "^3\.[89]\. ^3\.1[012]\." >nul
        if not errorlevel 1 (
            set PYTHON=python
            echo [OK] Uso Python di sistema: !PYVER!
        ) else (
            echo.
            echo  [ERRORE] Python !PYVER! non compatibile.
            echo  PyWebView richiede Python 3.8 - 3.12.
            echo.
            echo  Soluzione: installa Python 3.12 da:
            echo  https://www.python.org/downloads/release/python-3128/
            echo.
            echo  Scegli: "Windows installer (64-bit)"
            echo  Spunta: "Add python.exe to PATH"
            echo.
            pause
            exit /b 1
        )
    )
)

if "!PYTHON!"=="" (
    echo [ERRORE] Python non trovato.
    echo Installa Python 3.12 da https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [1/3] Installazione dipendenze...
!PYTHON! -m pip install --upgrade pip --quiet --no-warn-script-location
!PYTHON! -m pip install pyinstaller pywebview Pillow openpyxl xlsxwriter flask flask-socketio --quiet --no-warn-script-location

if errorlevel 1 (
    echo [ERRORE] Installazione dipendenze fallita
    pause
    exit /b 1
)

echo [2/3] Pulizia...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

echo [3/3] Compilazione...
!PYTHON! -m PyInstaller PerilCar.spec --clean --noconfirm

if errorlevel 1 (
    echo [ERRORE] Build fallita
    pause
    exit /b 1
)

echo.
echo  BUILD COMPLETATA!
echo  Eseguibile: dist\PerilCar\PerilCar.exe
echo.
pause
