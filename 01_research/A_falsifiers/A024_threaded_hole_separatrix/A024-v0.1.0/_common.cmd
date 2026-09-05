@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [SST-TH] Missing .venv. Run run_00_install.cmd first.
  exit /b 1
)
set "OMP_NUM_THREADS=16"
set "OPENBLAS_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
endlocal & set "PY=%PY%" & set "OMP_NUM_THREADS=16" & set "OPENBLAS_NUM_THREADS=1" & set "MKL_NUM_THREADS=1"
