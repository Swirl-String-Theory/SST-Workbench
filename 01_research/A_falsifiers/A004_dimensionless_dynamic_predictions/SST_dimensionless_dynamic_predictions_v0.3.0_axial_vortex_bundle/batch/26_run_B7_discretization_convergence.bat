@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
set OUT=%ROOT%\outputs\B7_discretization_convergence
echo === B7 DISCRETISATIECONVERGENTIE ===
echo Dit is een grotere statische campagne.
%PY_CMD% src\sst_axial_vortex_bundle.py campaign --config configs\B7_discretization_convergence.json --output "%OUT%"
if errorlevel 1 goto :fail
%PY_CMD% tools\analyze_bundle_modes.py --input outputs --output outputs\bundle_mode_analysis
start "" "%OUT%"
pause
exit /b 0
:fail
echo [ERROR] B7 faalde.
pause
exit /b 1
