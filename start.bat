@echo off
chcp 65001 >nul
title PerilCar ERP — Dev Server

echo.
echo  PerilCar ERP — Gestionale Aziendale
echo  Ing. Carmine Perillo
echo  ====================================
echo.

cd /d "%~dp0"

:: ── Verifica Python ──────────────────────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERRORE] Python non trovato!
    echo  Scaricalo da: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: ── Verifica dipendenze ───────────────────────────────────────────────
python -c "import flask, flask_socketio, watchdog" >nul 2>&1
if %errorlevel% neq 0 (
    echo  Installazione dipendenze...
    pip install flask flask-socketio watchdog --quiet
)

:: ── Avvia Ollama se non in esecuzione ────────────────────────────────
echo  Controllo Ollama (assistente AI)...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo  Avvio Ollama in background...
    where ollama >nul 2>&1
    if %errorlevel% equ 0 (
        start /B "" ollama serve >nul 2>&1
        timeout /t 3 /nobreak >nul
        echo  Ollama avviato.
    ) else (
        echo  Ollama non installato - assistente AI non disponibile.
        echo  Per installarlo: https://ollama.com/download
        echo  Poi: ollama pull llama3.2:1b
    )
) else (
    echo  Ollama gia attivo.
)

echo.
echo  ====================================
echo   Browser: http://localhost:5000
echo   Login:   admin / admin123
echo   Stop:    CTRL+C
echo  ====================================
echo.

python dev_server.py

echo.
pause
