@echo off
setlocal
cd /d "%~dp0"
if not defined OMP_NUM_THREADS set "OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%"
set "INPUT=%~1"
set "OUT=%~2"
if not exist ".venv\Scripts\python.exe" (echo [SST] .venv missing. Run run_install.cmd first.& exit /b 1)
if "%INPUT%"=="" (
  if "%OUT%"=="" (".venv\Scripts\python.exe" -m einstein_sst_gates.cli all --config config\basic.json) else (".venv\Scripts\python.exe" -m einstein_sst_gates.cli all --config config\basic.json --out "%OUT%")
) else (
  if "%OUT%"=="" (".venv\Scripts\python.exe" -m einstein_sst_gates.cli all --config config\basic.json --input "%INPUT%") else (".venv\Scripts\python.exe" -m einstein_sst_gates.cli all --config config\basic.json --input "%INPUT%" --out "%OUT%")
)
if errorlevel 1 exit /b 1
