@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONDONTWRITEBYTECODE=1"
set "OMP_NUM_THREADS=1"
set "OPENBLAS_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
if not "%~2"=="" set "SST_WORKBENCH_ROOT=%~2"
py -3.14 -B -m pytest tests -q -p no:cacheprovider
if errorlevel 1 exit /b 1
if /I "%~1"=="SELFTEST" exit /b 0
if not "%~1"=="" if /I not "%~1"=="ADMISSION_SMOKE" (
  echo [STOP] Only SELFTEST and ADMISSION_SMOKE are authorized. No FULL, CERTIFY or REVEAL.
  exit /b 2
)
py -3.14 -B run_migration.py
exit /b %ERRORLEVEL%
