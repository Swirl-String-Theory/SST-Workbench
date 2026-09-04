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
set "OUT=%ROOT%\outputs\infinite_background_vortex_quick"
if not exist "%OUT%" mkdir "%OUT%"
echo === INFINITE SOLID-BODY BACKGROUND VORTEX: QUICK PAIR ===
echo Test zeta*=0 versus zeta*=1/pi, met fixed sampled reach.
echo Verwachting: relative-equilibrium-residu blijft invariant.
%PY_CMD% src\sst_dimensionless_ratios.py campaign ^
  --config configs\infinite_background_vortex_quick.json ^
  --output "%OUT%"
if errorlevel 1 goto :fail
start "" "%OUT%"
pause
exit /b 0
:fail
echo [ERROR] Campagne faalde.
pause
exit /b 1
