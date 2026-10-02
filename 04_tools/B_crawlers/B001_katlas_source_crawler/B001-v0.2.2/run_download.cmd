@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
.venv\Scripts\python.exe -m katlas_source.cli --config config.json download
if errorlevel 1 exit /b %errorlevel%
