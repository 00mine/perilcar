@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title PerilCar ERP — Installazione

echo.
echo  ╔══════════════════════════════════════╗
echo  ║       PerilCar ERP — Installer       ║
echo  ║       Ing. Carmine Perillo           ║
echo  ╚══════════════════════════════════════╝
echo.

set INSTALL_DIR=%~dp0
cd /d "%INSTALL_DIR%"

REM ── Cerca Python 3.12 o 3.11 (percorsi standard) ─────────────────
set PYTHON=
for %%v in (312 311 310 39) do (
    if "!PYTHON!"=="" (
        for %%p in (
            "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python%%v-64\python.exe"
            "C:\Python%%v\python.exe"
            "C:\Program Files\Python%%v\python.exe"
            "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python%%v\python.exe"
        ) do (
            if "!PYTHON!"=="" if exist %%~p (
                set PYTHON=%%~p
                echo [OK] Python trovato: %%~p
            )
        )
    )
)

REM Prova anche python nel PATH se versione compatibile
if "!PYTHON!"=="" (
    python --version >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PVER=%%v
        echo !PVER! | findstr /r "^3\.[89]\." >nul && set PYTHON=python
        echo !PVER! | findstr /r "^3\.1[012]\." >nul && set PYTHON=python
    )
)

REM Python non trovato — scaricalo
if "!PYTHON!"=="" (
    echo.
    echo  Python non trovato. Download Python 3.12 in corso...
    echo  ^(circa 25 MB — attendere^)
    echo.
    set PY_URL=https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe
    set PY_INS=%TEMP%\python312_setup.exe
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest '!PY_URL!' -OutFile '!PY_INS!' -UseBasicParsing}"
    if exist "!PY_INS!" (
        echo  Installazione Python 3.12...
        "!PY_INS!" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1
        del "!PY_INS!" >nul 2>&1
        REM Aggiorna PATH per questa sessione
        set PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;!PATH!
        set PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
        echo  Python 3.12 installato.
    ) else (
        echo [ERRORE] Download fallito. Controlla la connessione internet.
        pause & exit /b 1
    )
)

echo.
echo [1/3] Installazione componenti PerilCar...
"!PYTHON!" -m pip install --quiet --upgrade pip --no-warn-script-location
"!PYTHON!" -m pip install --quiet flask flask-socketio Pillow openpyxl xlsxwriter --no-warn-script-location

if errorlevel 1 (
    echo [ERRORE] Installazione componenti fallita.
    pause & exit /b 1
)
echo  OK

REM ── Crea start.bat con percorso Python esatto ─────────────────────
echo [2/3] Creazione avviatore...
(
    echo @echo off
    echo cd /d "%INSTALL_DIR%"
    echo start "" /b "!PYTHON!" app_desktop.py
) > "%INSTALL_DIR%start.bat"
echo  OK

REM ── Crea collegamento Desktop ─────────────────────────────────────
echo [3/3] Collegamento Desktop...
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=%DESKTOP%\PerilCar ERP.lnk
set STARTER=%INSTALL_DIR%start.bat

powershell -Command "& { $ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = 'cmd.exe'; $s.Arguments = '/c \"\"!STARTER!\"\"'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.WindowStyle = 7; $s.IconLocation = '%INSTALL_DIR%icon.ico'; $s.Description = 'PerilCar ERP'; $s.Save() }"

echo  OK

echo.
echo  ╔══════════════════════════════════════╗
echo  ║      INSTALLAZIONE COMPLETATA!       ║
echo  ╚══════════════════════════════════════╝
echo.
echo  Icona "PerilCar ERP" aggiunta al Desktop.
echo.
echo  PROSSIMI PASSI:
echo  1. Doppio click su CONFIGURA_NAS.bat
echo  2. Doppio click su "PerilCar ERP" sul Desktop
echo.
echo  Accesso iniziale:
echo    Username: admin
echo    Password: admin123
echo.
pause
