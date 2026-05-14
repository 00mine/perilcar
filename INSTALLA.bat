@echo off
setlocal enabledelayedexpansion
title PerilCar ERP - Installazione

echo.
echo  ================================================
echo   PerilCar ERP - Installazione
echo   Ing. Carmine Perillo
echo  ================================================
echo.

set INSTALL_DIR=%~dp0
cd /d "%INSTALL_DIR%"

echo Ricerca Python in corso...
echo.

set PYTHON=

REM Cerca Python 3.12
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
    goto :found
)
if exist "C:\Python312\python.exe" (
    set PYTHON=C:\Python312\python.exe
    goto :found
)

REM Cerca Python 3.11
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    goto :found
)
if exist "C:\Python311\python.exe" (
    set PYTHON=C:\Python311\python.exe
    goto :found
)

REM Cerca Python 3.10
if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
    goto :found
)

REM Prova python nel PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto :found
)

REM Python non trovato - scaricalo
echo Python non trovato. Download in corso...
echo Attendere circa 1 minuto...
echo.

set PY_URL=https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe
set PY_INS=%TEMP%\python312.exe

powershell -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; (New-Object Net.WebClient).DownloadFile('%PY_URL%', '%PY_INS%')"

if not exist "%PY_INS%" (
    echo.
    echo ERRORE: Download Python fallito.
    echo Connettiti a internet e riprova.
    pause
    exit /b 1
)

echo Installazione Python 3.12...
"%PY_INS%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%PY_INS%" >nul 2>&1

set PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if not exist "%PYTHON%" set PYTHON=python

:found
echo Python trovato: %PYTHON%
echo.

echo [1/3] Installazione componenti...
"%PYTHON%" -m pip install --quiet --upgrade pip
"%PYTHON%" -m pip install --quiet flask flask-socketio Pillow openpyxl xlsxwriter

if errorlevel 1 (
    echo ERRORE installazione componenti.
    pause
    exit /b 1
)
echo OK

echo [2/3] Creazione avviatore...
(
    echo @echo off
    echo cd /d "%INSTALL_DIR%"
    echo start "" /b "%PYTHON%" app_desktop.py
) > "%INSTALL_DIR%start.bat"
echo OK

echo [3/3] Collegamento Desktop...
set SHORTCUT=%USERPROFILE%\Desktop\PerilCar ERP.lnk

powershell -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath='%INSTALL_DIR%start.bat'; $s.WorkingDirectory='%INSTALL_DIR%'; $s.IconLocation='%INSTALL_DIR%icon.ico'; $s.Save()"

echo OK

echo.
echo  ================================================
echo   INSTALLAZIONE COMPLETATA
echo  ================================================
echo.
echo  Icona PerilCar ERP aggiunta al Desktop.
echo.
echo  PROSSIMI PASSI:
echo  1. Doppio click su CONFIGURA_NAS.bat
echo  2. Doppio click su PerilCar ERP sul Desktop
echo.
echo  Username: admin
echo  Password: admin123
echo.
pause
