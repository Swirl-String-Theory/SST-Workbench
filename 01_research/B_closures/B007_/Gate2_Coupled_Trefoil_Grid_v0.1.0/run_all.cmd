@echo off
setlocal
cd /d "%~dp0"
set NUMBA_NUM_THREADS=2
set OMP_NUM_THREADS=2
python -m pytest -q tests
if errorlevel 1 exit /b 1
python src\euler_coupled.py --seed both --n 32 --steps 3 --out "Gate2_Coupled_Trefoil_Grid_v0.1.0-outputs"
if errorlevel 1 exit /b 1
exit /b 0
