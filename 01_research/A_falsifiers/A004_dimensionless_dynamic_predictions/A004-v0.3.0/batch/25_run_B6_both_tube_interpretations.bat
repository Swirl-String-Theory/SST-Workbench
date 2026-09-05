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
echo === B6A: FYSIEKE BUIZEN ===
%PY_CMD% src\sst_axial_vortex_bundle.py campaign --config configs\B6_physical_tubes.json --output outputs\bundle_physical_tubes
if errorlevel 1 goto :fail
echo === B6B: NUMERIEKE DISCRETISATIE ===
%PY_CMD% src\sst_axial_vortex_bundle.py campaign --config configs\B6_numerical_discretization.json --output outputs\bundle_numerical_discretization
if errorlevel 1 goto :fail
%PY_CMD% tools\analyze_bundle_modes.py --input outputs --output outputs\bundle_mode_analysis
if errorlevel 1 goto :fail
start "" "%ROOT%\outputs\bundle_mode_analysis"
pause
exit /b 0
:fail
echo [ERROR] B6 werd afgebroken.
pause
exit /b 1
