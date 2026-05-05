@echo off
chcp 65001 >nul
title PerilCar ERP — Dev Server

echo.
echo  ██████╗ ███████╗██████╗ ██╗██╗      ██████╗ █████╗ ██████╗
echo  ██╔══██╗██╔════╝██╔══██╗██║██║     ██╔════╝██╔══██╗██╔══██╗
echo  ██████╔╝█████╗  ██████╔╝██║██║     ██║     ███████║██████╔╝
echo  ██╔═══╝ ██╔══╝  ██╔══██╗██║██║     ██║     ██╔══██║██╔══██╗
echo  ██║     ███████╗██║  ██║██║███████╗╚██████╗██║  ██║██║  ██║
echo  ╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝
echo.
echo  Gestionale Aziendale — Ing. Carmine Perillo
echo  ============================================
echo.

:: ── Verifica Python ──────────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRORE] Python non trovato!
    echo  Scaricalo da: https://www.python.org/downloads/
    echo  Assicurati di spuntare "Add Python to PATH" durante l'installazione.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Python trovato: %PYVER%

:: ── Controlla/installa dipendenze ────────────────────────────────────
echo.
echo  Controllo dipendenze...
python -c "import flask, flask_socketio, watchdog" >nul 2>&1
if %errorlevel% neq 0 (
    echo  Installazione dipendenze in corso...
    pip install flask flask-socketio watchdog customtkinter pillow --quiet
    if %errorlevel% neq 0 (
        echo  [ERRORE] Installazione dipendenze fallita.
        pause
        exit /b 1
    )
    echo  Dipendenze installate!
) else (
    echo  Dipendenze OK.
)

:: ── Vai nella cartella del progetto ──────────────────────────────────
cd /d "%~dp0"
echo.
echo  Directory: %CD%
echo.

:: ── Avvio server ──────────────────────────────────────────────────────
echo  ============================================
echo   Avvio PerilCar Dev Server...
echo   Browser: http://localhost:5000
echo   Login:   admin / admin123
echo.
echo   Per fermare: premi CTRL+C
echo  ============================================
echo.

python dev_server.py

echo.
echo  Server fermato.
pause
