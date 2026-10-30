@echo off
setlocal
cd /d "%~dp0"
set "OMP_NUM_THREADS=1"
set "OPENBLAS_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
set "PYTHONDONTWRITEBYTECODE=1"
py -3.14 -B run_tests.py || exit /b 1
if /i "%~1"=="SELFTEST" exit /b 0
if not "%~1"=="" if /i not "%~1"=="BASIC" (echo Only BASIC or SELFTEST is authorized for this version. & exit /b 2)
py -3.14 -B run_reported.py
exit /b %ERRORLEVEL%
