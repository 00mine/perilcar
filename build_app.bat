@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title PerilCar ERP - Build

echo.
echo  PerilCar ERP - Build App Desktop
echo  ========================================
echo.

REM ─── Cerca Python 3.12 o 3.11 (percorsi standard Windows) ───────────
set PYTHON=

REM Percorsi dove Windows installa Python per utente singolo
for %%v in (312 311 310) do (
    if "!PYTHON!"=="" (
        for %%p in (
            "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python%%v-64\python.exe"
            "C:\Python%%v\python.exe"
            "C:\Program Files\Python%%v\python.exe"
            "C:\Program Files (x86)\Python%%v\python.exe"
        ) do (
            if "!PYTHON!"=="" if exist %%p (
                set PYTHON=%%p
                echo [OK] Python trovato: %%p
            )
        )
    )
)

if "!PYTHON!"=="" (
    echo.
    echo  [ERRORE] Python 3.10/3.11/3.12 non trovato.
    echo.
    echo  Installa Python 3.12 da:
    echo  https://www.python.org/downloads/release/python-3128/
    echo.
    echo  "Windows installer (64-bit)" + spunta "Add python.exe to PATH"
    echo.
    pause
    exit /b 1
)

echo.
echo [1/3] Installazione dipendenze...
!PYTHON! -m pip install --upgrade pip --quiet --no-warn-script-location
!PYTHON! -m pip install pyinstaller pywebview Pillow openpyxl xlsxwriter flask flask-socketio --quiet --no-warn-script-location

if errorlevel 1 (
    echo [ERRORE] Dipendenze fallite
    pause
    exit /b 1
)

echo [2/3] Pulizia...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

echo [3/3] Compilazione (2-3 minuti)...
!PYTHON! -m PyInstaller PerilCar.spec --clean --noconfirm

if errorlevel 1 (
    echo [ERRORE] Build fallita
    pause
    exit /b 1
)

echo.
echo  BUILD COMPLETATA!
echo  dist\PerilCar\PerilCar.exe
echo.
pause
