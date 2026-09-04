@echo off
setlocal
cd /d "%~dp0"
set "RUN=%~1"
if "%RUN%"=="" (".venv\Scripts\python.exe" -m einstein_sst_gates.cli reveal) else (".venv\Scripts\python.exe" -m einstein_sst_gates.cli reveal --run "%RUN%")
