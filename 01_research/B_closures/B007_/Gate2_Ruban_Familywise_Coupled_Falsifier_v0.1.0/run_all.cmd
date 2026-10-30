@echo off
setlocal
cd /d "%~dp0"
set NUMBA_NUM_THREADS=1
set OMP_NUM_THREADS=1
set OPENBLAS_NUM_THREADS=1
set MKL_NUM_THREADS=1
py -m pytest -q tests
if errorlevel 1 exit /b %errorlevel%
py src\falsifier.py
if errorlevel 1 exit /b %errorlevel%
py src\make_report.py
if errorlevel 1 exit /b %errorlevel%
py src\pack_outputs.py
exit /b %errorlevel%
