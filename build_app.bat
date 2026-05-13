@echo off
REM PerilCar ERP — Build App Desktop
REM Crea PerilCar.exe in dist\PerilCar\

setlocal
chcp 65001 >nul 2>&1
echo ===================================================
echo  PerilCar ERP - Build App Desktop
echo ===================================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Python non trovato.
    echo Installa Python 3.11 o 3.12 da https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Mostra versione Python
echo Python in uso:
python --version
echo.

REM Avviso versione Python
for /f "tokens=2" %%i in ('python --version') do set PYVER=%%i
echo Versione: %PYVER%
echo.
echo NOTA: PyWebView funziona meglio con Python 3.11 o 3.12.
echo Se hai problemi con Python 3.13+ usa Python 3.12 (LTS).
echo.

REM Installa dipendenze
echo [1/3] Installazione dipendenze...
python -m pip install --upgrade pip --quiet
python -m pip install --upgrade pyinstaller --quiet
python -m pip install --upgrade pywebview --quiet
python -m pip install --upgrade Pillow openpyxl xlsxwriter flask flask-socketio --quiet

if errorlevel 1 (
    echo.
    echo [ERRORE] Installazione dipendenze fallita.
    echo.
    echo SOLUZIONE: Se vedi errori su 'pythonnet', stai usando Python 3.13+
    echo che non e' ancora supportato da PyWebView su Windows.
    echo Installa Python 3.12 da https://www.python.org/downloads/release/python-3128/
    echo e riprova.
    pause
    exit /b 1
)

REM Pulizia
echo [2/3] Pulizia build precedente...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

REM Build
echo [3/3] Compilazione (2-3 minuti)...
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
echo Eseguibile: dist\PerilCar\PerilCar.exe
echo.
pause
