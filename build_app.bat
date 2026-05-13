@echo off
REM PerilCar ERP — Compilazione App Desktop
REM Genera PerilCar.exe nella cartella dist/PerilCar/

echo ===================================================
echo  PerilCar ERP - Build App Desktop
echo ===================================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato. Installalo da python.org
    pause
    exit /b 1
)

REM Installa/aggiorna dipendenze di build
echo [1/3] Installazione dipendenze...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet pyinstaller pywebview Pillow openpyxl xlsxwriter flask flask-socketio

REM Pulisci build precedente
echo [2/3] Pulizia build precedente...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

REM Build
echo [3/3] Compilazione in corso (richiede 2-3 minuti)...
python -m PyInstaller PerilCar.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERRORE] Build fallita
    pause
    exit /b 1
)

echo.
echo ===================================================
echo  BUILD COMPLETATA
echo ===================================================
echo.
echo Eseguibile creato in: dist\PerilCar\PerilCar.exe
echo.
echo Per testare: dist\PerilCar\PerilCar.exe
echo.
pause
