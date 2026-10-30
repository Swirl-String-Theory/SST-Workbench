@echo off
setlocal
set "OMP_NUM_THREADS=1"
set "OPENBLAS_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
py -3.14 -B "%~dp0run_framework_smoke.py"
exit /b %errorlevel%
