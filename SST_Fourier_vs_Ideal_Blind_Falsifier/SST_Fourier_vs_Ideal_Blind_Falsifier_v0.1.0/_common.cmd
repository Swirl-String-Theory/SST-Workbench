@echo off
setlocal
cd /d "%~dp0"
if not defined OMP_NUM_THREADS set "OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%"
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [SST-FVI] Missing .venv. Run run_00_install.cmd first.
  exit /b 2
)
endlocal & set "PY=%~dp0.venv\Scripts\python.exe"
