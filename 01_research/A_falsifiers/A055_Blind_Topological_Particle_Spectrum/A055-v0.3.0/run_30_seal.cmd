@echo off
setlocal
cd /d "%~dp0"
set PRESET=%~1
if "%PRESET%"=="" set PRESET=quick
.venv\Scripts\python.exe -m a055_spectrum.cli seal --config configs/%PRESET%.json
