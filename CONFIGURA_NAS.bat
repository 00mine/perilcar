@echo off
setlocal enabledelayedexpansion
title PerilCar ERP - Configurazione NAS

echo.
echo  ================================================
echo   PerilCar ERP - Configurazione NAS
echo  ================================================
echo.

set NAS_IP=192.168.1.250
set NAS_CARTELLA=datinas
set NAS_PATH=\\%NAS_IP%\%NAS_CARTELLA%\perilcar
set INSTALL_DIR=%~dp0
cd /d "%INSTALL_DIR%"

echo [1/4] Verifica connessione NAS (%NAS_IP%)...
ping -n 1 %NAS_IP% >nul 2>&1
if errorlevel 1 (
    echo ERRORE: NAS non raggiungibile.
    echo Verifica che il NAS sia acceso e il PC sia in rete.
    pause
    exit /b 1
)
echo OK - NAS raggiungibile

echo [2/4] Creazione cartelle su NAS...
if not exist "%NAS_PATH%" mkdir "%NAS_PATH%" 2>nul
if not exist "%NAS_PATH%\db" mkdir "%NAS_PATH%\db" 2>nul
if not exist "%NAS_PATH%\uploads" mkdir "%NAS_PATH%\uploads" 2>nul
if not exist "%NAS_PATH%\backup" mkdir "%NAS_PATH%\backup" 2>nul
echo OK

echo [3/4] Migrazione database...
if exist "%INSTALL_DIR%db\perilcar.db" (
    if not exist "%NAS_PATH%\db\perilcar.db" (
        copy "%INSTALL_DIR%db\perilcar.db" "%NAS_PATH%\db\perilcar.db" >nul
        echo DB copiato sul NAS
    ) else (
        echo DB gia presente sul NAS
    )
)
if exist "%INSTALL_DIR%db\demolizioni.db" (
    if not exist "%NAS_PATH%\db\demolizioni.db" (
        copy "%INSTALL_DIR%db\demolizioni.db" "%NAS_PATH%\db\demolizioni.db" >nul
    )
)
echo OK

echo [4/4] Aggiornamento configurazione...
if not exist "%INSTALL_DIR%config" mkdir "%INSTALL_DIR%config"

(
echo {
echo   "db_path": "\\\\%NAS_IP%\\%NAS_CARTELLA%\\perilcar\\db\\perilcar.db",
echo   "backup_dir": "\\\\%NAS_IP%\\%NAS_CARTELLA%\\perilcar\\backup",
echo   "log_dir": "logs",
echo   "backup_auto": true,
echo   "backup_interval_ore": 24,
echo   "nas": {
echo     "abilitato": true,
echo     "ip": "%NAS_IP%",
echo     "cartella": "%NAS_CARTELLA%",
echo     "percorso_db": "\\\\%NAS_IP%\\%NAS_CARTELLA%\\perilcar\\db",
echo     "percorso_uploads": "\\\\%NAS_IP%\\%NAS_CARTELLA%\\perilcar\\uploads"
echo   }
echo }
) > "%INSTALL_DIR%config\settings.json"
echo OK

echo.
echo  ================================================
echo   CONFIGURAZIONE NAS COMPLETATA
echo  ================================================
echo.
echo  PerilCar ora usa il NAS per:
echo   Database: %NAS_PATH%\db\
echo   Foto:     %NAS_PATH%\uploads\
echo   Backup:   %NAS_PATH%\backup\
echo.
echo  Avvia PerilCar ERP dal Desktop.
echo.
pause
