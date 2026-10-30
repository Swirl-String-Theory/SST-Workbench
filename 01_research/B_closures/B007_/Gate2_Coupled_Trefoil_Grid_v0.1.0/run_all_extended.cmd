@echo off
setlocal
cd /d "%~dp0"
set NUMBA_NUM_THREADS=2
set OMP_NUM_THREADS=2
python src\euler_coupled.py --seed both --n 48 --steps 3 --out "Gate2_Coupled_Trefoil_Grid_v0.1.0-outputs"
if errorlevel 1 exit /b 1
python src\euler_coupled.py --seed both --n 64 --steps 3 --out "Gate2_Coupled_Trefoil_Grid_v0.1.0-outputs"
if errorlevel 1 exit /b 1
python src\euler_coupled.py --seed T_2_3_B1600_N512 --n 48 --dt 0.0015 --steps 6 --out "Gate2_Coupled_Trefoil_Grid_v0.1.0-outputs\time_refinement"
if errorlevel 1 exit /b 1
python src\euler_coupled.py --seed T_2_3_B1600_N512 --n 32 --gamma-bg -0.05 --out "Gate2_Coupled_Trefoil_Grid_v0.1.0-outputs\circulation_sensitivity\negative"
if errorlevel 1 exit /b 1
python src\euler_coupled.py --seed T_2_3_B1600_N512 --n 32 --gamma-bg 0.20 --out "Gate2_Coupled_Trefoil_Grid_v0.1.0-outputs\circulation_sensitivity\strong_positive"
if errorlevel 1 exit /b 1
python src\assess.py
if errorlevel 1 exit /b 1
exit /b 0
