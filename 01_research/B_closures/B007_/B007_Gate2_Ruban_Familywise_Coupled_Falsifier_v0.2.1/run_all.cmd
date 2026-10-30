@echo off
setlocal
cd /d "%~dp0"
set "OMP_NUM_THREADS=1"
set "OPENBLAS_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
set "NUMBA_NUM_THREADS=1"
if "%~1"=="" (
  echo Default pilot: T_2_3 with 16 B0 x 5 Lambda, then promote N2048.
  echo See README.md for family, fine, resolution and coupled arguments.
)
py -m pytest -q tests
if errorlevel 1 ( echo Tests failed. No falsifier run. & exit /b 1 )
py -m src.pipeline %*
if errorlevel 1 ( echo Pipeline failed. Gate 2 remains UNRESOLVED. & exit /b 1 )
exit /b 0
