@echo off
chcp 65001 >nul
title PerilCar — Import Excel

echo.
echo  PerilCar ERP — Import Excel Diretto
echo  ====================================
echo.

cd /d "%~dp0"

:: Cerca il file Excel automaticamente
set EXCEL_FILE=

:: Prima prova nella cartella perilcar
if exist "DANEA_.xlsx" set EXCEL_FILE=DANEA_.xlsx
if exist "magazzino.xlsx" set EXCEL_FILE=magazzino.xlsx
if exist "export.xlsx" set EXCEL_FILE=export.xlsx

:: Se non trovato, chiedi all'utente
if "%EXCEL_FILE%"=="" (
    echo  Nessun file Excel trovato automaticamente.
    echo.
    echo  Trascina qui il file Excel e premi Invio,
    set /p EXCEL_FILE="  oppure scrivi il percorso completo: "
)

if "%EXCEL_FILE%"=="" (
    echo  Nessun file specificato. Uscita.
    pause
    exit /b 1
)

echo.
echo  File selezionato: %EXCEL_FILE%
echo.
echo  Avvio import... (non chiudere questa finestra)
echo.

python import_excel.py "%EXCEL_FILE%"

echo.
pause
