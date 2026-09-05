@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set PRESET=quick
if /I "%~1"=="full" set PRESET=full
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe run_dependency_preflight.py >nul 2>&1
if errorlevel 1 call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
call "cmd\01_BUILD_CPP.cmd"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe run_native_preflight.py >nul
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe run_phase4.py --preset %PRESET%
exit /b %errorlevel%
