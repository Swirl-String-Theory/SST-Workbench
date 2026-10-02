@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Voer eerst batch\01_setup_venv.bat uit.
  pause
  exit /b 1
)
set "OUT=%ROOT%\outputs\infinite_background_vortex_ladder"
if not exist "%OUT%" mkdir "%OUT%"
echo === BACKGROUND VORTICITY LADDER ===
echo zeta* = {-2,-1,-0.5,0,0.5,1,2}/pi
echo Dit is een statische covariance/falsificatiecampagne.
%PY_CMD% src\sst_dimensionless_ratios.py campaign ^
  --config configs\infinite_background_vortex_ladder.json ^
  --output "%OUT%"
if errorlevel 1 goto :fail
start "" "%OUT%"
pause
exit /b 0
:fail
echo [ERROR] Campagne faalde.
pause
exit /b 1
