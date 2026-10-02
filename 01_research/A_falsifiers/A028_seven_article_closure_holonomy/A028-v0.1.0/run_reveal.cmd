@echo off
setlocal
cd /d "%~dp0"
set "RUN=%~1"
if "%RUN%"=="" set "RUN=results\basic"
if not exist ".venv\Scripts\python.exe" call run_00_install.cmd || exit /b 1
.venv\Scripts\python.exe scripts\reveal.py --run-dir "%RUN%"
