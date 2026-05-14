@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Cerca Python compatibile
set PYTHON=
for %%v in (312 311 310 39) do (
    if "!PYTHON!"=="" (
        for %%p in (
            "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe"
            "C:\Python%%v\python.exe"
            "C:\Program Files\Python%%v\python.exe"
        ) do (
            if "!PYTHON!"=="" if exist %%~p set PYTHON=%%~p
        )
    )
)

if "!PYTHON!"=="" (
    python --version >nul 2>&1
    if not errorlevel 1 set PYTHON=python
)

if "!PYTHON!"=="" (
    echo Python non trovato. Esegui prima INSTALLA.bat
    pause & exit /b 1
)

start "" /b "!PYTHON!" app_desktop.py
