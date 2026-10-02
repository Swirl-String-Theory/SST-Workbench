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
set "OUT=%ROOT%\outputs\infinite_background_vortex_evolution"
if not exist "%OUT%" mkdir "%OUT%"
echo === TREFOIL EVOLUTION: zeta*=0 versus 1/pi ===
echo De recurrence-fit verwijdert globale rotatie.
%PY_CMD% src\sst_dimensionless_ratios.py campaign ^
  --config configs\infinite_background_vortex_evolution.json ^
  --output "%OUT%"
if errorlevel 1 goto :fail
start "" "%OUT%"
pause
exit /b 0
:fail
echo [ERROR] Campagne faalde.
pause
exit /b 1
