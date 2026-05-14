@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title PerilCar ERP — Configurazione NAS

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   PerilCar ERP — Configurazione NAS  ║
echo  ╚══════════════════════════════════════╝
echo.
echo  Questo script collega PerilCar al NAS aziendale.
echo  I dati (magazzino, demolizioni, foto) verranno
echo  salvati sul NAS condiviso da tutti i PC.
echo.

set NAS_IP=192.168.1.250
set NAS_CARTELLA=datinas
set NAS_PATH=\\%NAS_IP%\%NAS_CARTELLA%\perilcar

REM ── Verifica connessione al NAS ───────────────────────────────────
echo [1/4] Verifica connessione al NAS (%NAS_IP%)...
ping -n 1 %NAS_IP% >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERRORE] NAS non raggiungibile (%NAS_IP%)
    echo  Verifica che:
    echo   - Il NAS sia acceso
    echo   - Il PC sia sulla stessa rete
    echo   - L'IP %NAS_IP% sia corretto
    echo.
    pause
    exit /b 1
)
echo  OK — NAS raggiungibile

REM ── Crea cartelle sul NAS ─────────────────────────────────────────
echo [2/4] Creazione cartelle su NAS...
if not exist "%NAS_PATH%"         mkdir "%NAS_PATH%"         2>nul
if not exist "%NAS_PATH%\db"      mkdir "%NAS_PATH%\db"      2>nul
if not exist "%NAS_PATH%\uploads" mkdir "%NAS_PATH%\uploads" 2>nul
if not exist "%NAS_PATH%\backup"  mkdir "%NAS_PATH%\backup"  2>nul

if not exist "%NAS_PATH%\db" (
    echo  [ERRORE] Impossibile creare cartelle sul NAS.
    echo  Verifica le credenziali di accesso alla cartella %NAS_CARTELLA%.
    pause
    exit /b 1
)
echo  OK — Cartelle create: %NAS_PATH%

REM ── Sposta DB esistenti sul NAS (solo se locali e NAS vuoto) ──────
echo [3/4] Migrazione database...
set LOCAL_DB=%~dp0db\perilcar.db
set NAS_DB=%NAS_PATH%\db\perilcar.db

if exist "%LOCAL_DB%" (
    if not exist "%NAS_DB%" (
        echo  Copio DB locale sul NAS...
        copy "%LOCAL_DB%" "%NAS_DB%" >nul
        copy "%~dp0db\demolizioni.db" "%NAS_PATH%\db\demolizioni.db" >nul 2>&1
        echo  OK — Database copiati sul NAS
    ) else (
        echo  DB gia presente sul NAS — nessuna copia necessaria
    )
) else (
    echo  Nessun DB locale — il NAS sara usato direttamente
)

REM ── Aggiorna settings.json ────────────────────────────────────────
echo [4/4] Aggiornamento configurazione...

set CONFIG_DIR=%~dp0config
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

REM Scrivi settings.json con percorsi NAS
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
) > "%CONFIG_DIR%\settings.json"

echo  OK — Configurazione salvata

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   CONFIGURAZIONE NAS COMPLETATA!     ║
echo  ╚══════════════════════════════════════╝
echo.
echo  PerilCar ERP ora usa il NAS per:
echo   Database: %NAS_PATH%\db\
echo   Foto:     %NAS_PATH%\uploads\
echo   Backup:   %NAS_PATH%\backup\
echo.
echo  Avvia PerilCar normalmente con start.bat
echo  Tutti i PC configurati con questo script
echo  vedranno gli stessi dati in tempo reale.
echo.
pause
