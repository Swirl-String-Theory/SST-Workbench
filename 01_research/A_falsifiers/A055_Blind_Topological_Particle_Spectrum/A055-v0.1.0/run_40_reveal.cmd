@echo off
setlocal
cd /d "%~dp0"
set PRESET=%~1
if "%PRESET%"=="" set PRESET=basic
.venv\Scripts\python.exe -m a054_spectrum.cli reveal --config configs/%PRESET%.json
