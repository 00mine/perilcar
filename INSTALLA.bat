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
echo  Questo installer configurera' il programma
echo  sul tuo computer. Non serve installare altro.
echo.
echo  Premi un tasto per continuare...
pause >nul

REM ─── Percorso di installazione ───────────────────────────────────────
set INSTALL_DIR=C:\PerilCar
echo.
echo  Cartella installazione: %INSTALL_DIR%
echo.

REM ─── Crea cartella ───────────────────────────────────────────────────
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\db" mkdir "%INSTALL_DIR%\db"
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"
if not exist "%INSTALL_DIR%\backup" mkdir "%INSTALL_DIR%\backup"

REM ─── Copia file app ──────────────────────────────────────────────────
echo [1/4] Copia file applicazione...
xcopy /E /I /Y /Q "%~dp0*" "%INSTALL_DIR%\" >nul 2>&1

REM ─── Verifica Python compatibile (3.8-3.12) ──────────────────────────
echo [2/4] Verifica Python...
set PYTHON=
set GOOD_PY=0

REM Cerca Python 3.12 o 3.11 installato
for %%v in (312 311 310 39 38) do (
    if !GOOD_PY!==0 (
        for %%p in (
            "C:\Python%%~v\python.exe"
            "C:\Program Files\Python%%~v\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python%%~v\python.exe"
        ) do (
            if !GOOD_PY!==0 if exist %%p (
                set PYTHON=%%p
                set GOOD_PY=1
            )
        )
    )
)

REM Prova anche python nel PATH
if !GOOD_PY!==0 (
    python --version >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PVER=%%v
        echo !PVER! | findstr /r "^3\.[89]\. ^3\.1[012]\." >nul
        if not errorlevel 1 (
            set PYTHON=python
            set GOOD_PY=1
        )
    )
)

REM Se Python non trovato/incompatibile → scaricalo automaticamente
if !GOOD_PY!==0 (
    echo.
    echo  Python compatibile non trovato.
    echo  Download Python 3.12 in corso...
    echo  (circa 25 MB — attendere)
    echo.
    
    REM Scarica Python 3.12 installer
    set PY_URL=https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe
    set PY_INS=%TEMP%\python312_setup.exe
    
    REM Usa PowerShell per download
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest '%PY_URL%' -OutFile '%PY_INS%' -UseBasicParsing}"
    
    if not exist "%PY_INS%" (
        echo [ERRORE] Download Python fallito.
        echo Installa Python 3.12 manualmente da:
        echo https://www.python.org/downloads/release/python-3128/
        pause
        exit /b 1
    )
    
    echo  Installazione Python 3.12 in corso...
    "%PY_INS%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1
    del "%PY_INS%" >nul 2>&1
    
    REM Riprova ricerca Python
    for %%p in (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "C:\Python312\python.exe"
    ) do (
        if !GOOD_PY!==0 if exist %%p (
            set PYTHON=%%p
            set GOOD_PY=1
        )
    )
    
    if !GOOD_PY!==0 (
        echo [ERRORE] Installazione Python fallita.
        pause
        exit /b 1
    )
    echo  Python 3.12 installato correttamente.
)

echo  Python OK: !PYTHON!

REM ─── Installa dipendenze Python ───────────────────────────────────────
echo [3/4] Installazione componenti PerilCar...
!PYTHON! -m pip install --quiet --no-warn-script-location ^
    pywebview flask flask-socketio ^
    Pillow openpyxl xlsxwriter

if errorlevel 1 (
    echo [ERRORE] Installazione componenti fallita
    pause
    exit /b 1
)

REM ─── Crea collegamento sul Desktop ───────────────────────────────────
echo [4/4] Creazione collegamento Desktop...

REM Crea il file .bat di avvio silenzioso
set STARTER=%INSTALL_DIR%\PerilCar.bat
echo @echo off > "%STARTER%"
echo cd /d "%INSTALL_DIR%" >> "%STARTER%"
echo start "" "!PYTHON!" "%INSTALL_DIR%\app_desktop.py" >> "%STARTER%"

REM Crea shortcut sul Desktop tramite PowerShell
set DESKTOP=%USERPROFILE%\Desktop
powershell -Command "& { ^
    $s = (New-Object -COM WScript.Shell).CreateShortcut('%DESKTOP%\PerilCar ERP.lnk'); ^
    $s.TargetPath = 'cmd.exe'; ^
    $s.Arguments = '/c cd /d ""%INSTALL_DIR%"" && start /b \"\" \"!PYTHON!\" app_desktop.py'; ^
    $s.WorkingDirectory = '%INSTALL_DIR%'; ^
    $s.WindowStyle = 7; ^
    $s.Description = 'PerilCar ERP Gestionale'; ^
    $s.Save() ^
}"

echo.
echo  ╔══════════════════════════════════════╗
echo  ║      INSTALLAZIONE COMPLETATA!       ║
echo  ╚══════════════════════════════════════╝
echo.
echo  Icona "PerilCar ERP" aggiunta al Desktop.
echo  Doppio click sull'icona per avviare.
echo.
echo  Accesso iniziale:
echo    Username: admin
echo    Password: admin123
echo.
echo  Cambia la password al primo accesso!
echo.
pause
