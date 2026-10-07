@echo off
setlocal
cd /d "%~dp0"
set PRESET=%~1
if "%PRESET%"=="" set PRESET=quick
.venv\Scripts\python.exe -m a055_spectrum.cli reveal --config configs/%PRESET%.json
