@echo off
setlocal
cd /d "%~dp0"
set PRESET=%~1
if "%PRESET%"=="" set PRESET=basic
if not exist .venv\Scripts\python.exe call run_00_install.cmd || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli selftest --force-python || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli blind --config configs/%PRESET%.json --force-python --overwrite || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli seal --config configs/%PRESET%.json || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli reveal --config configs/%PRESET%.json || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli package --config configs/%PRESET%.json || exit /b 1
