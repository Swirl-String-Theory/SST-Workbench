@echo off
setlocal
cd /d "%~dp0"
if not defined A069_XPU_PYTHON set "A069_XPU_PYTHON=%~dp0.venv-xpu\Scripts\python.exe"
if not exist "%A069_XPU_PYTHON%" (echo XPU Python missing: "%A069_XPU_PYTHON%" & echo Set A069_XPU_PYTHON to your tested .venv-xpu\Scripts\python.exe & exit /b 2)
set "BASE=C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A069_3D_SwirlClock_Emergence\A069_v0.6.2\results\checkpoints"
set "B=%BASE%\B160\20261019T142950548208Z\T000016.npz"
set "A=%BASE%\A160\20261019T143016722791Z\T000016.npz"
if not exist "%B%" (echo Missing B160 checkpoint: "%B%" & exit /b 3)
if not exist "%A%" (echo Missing A160 checkpoint: "%A%" & exit /b 3)
"%A069_XPU_PYTHON%" gp_full_xpu.py --case B160 --init checkpoint --checkpoint "%B%" --total-steps 32 --diagnostic-every 4 --checkpoint-every 8 --cpu-parity-steps 2
if errorlevel 1 exit /b %errorlevel%
"%A069_XPU_PYTHON%" gp_full_xpu.py --case A160 --init checkpoint --checkpoint "%A%" --total-steps 32 --diagnostic-every 4 --checkpoint-every 8 --cpu-parity-steps 2 --allow-unqualified-geometry
if errorlevel 1 exit /b %errorlevel%
echo Both GPU checkpoint continuations finished. G34 and G35 remain UNRESOLVED.
endlocal
