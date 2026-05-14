@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set PYTHON=
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
if "!PYTHON!"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
if "!PYTHON!"=="" if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" set PYTHON=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
if "!PYTHON!"=="" set PYTHON=python

REM Avvia senza finestra terminale visibile
start "" /b pythonw "%~dp0app_desktop.py" >nul 2>&1
if errorlevel 1 start "" /b "!PYTHON!" "%~dp0app_desktop.py"
