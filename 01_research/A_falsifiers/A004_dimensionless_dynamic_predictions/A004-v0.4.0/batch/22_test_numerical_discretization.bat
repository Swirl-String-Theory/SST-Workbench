@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
if not exist "%ROOT%\.venv\Scripts\python.exe" (
  echo [ERROR] Voer eerst batch\01_setup_venv.bat uit.
  pause
  exit /b 1
)
set OUT=%ROOT%\outputs\bundle_numerical_discretization
echo === NUMERIEKE DISCRETISATIE ===
echo Totale circulatie blijft vast; Gamma per buis is Gamma_total / N.
%PY_CMD% src\sst_axial_vortex_bundle.py campaign --config configs\B6_numerical_discretization.json --output "%OUT%"
if errorlevel 1 goto :fail
start "" "%OUT%"
pause
exit /b 0
:fail
echo [ERROR] Discretisatiecampagne faalde.
pause
exit /b 1
