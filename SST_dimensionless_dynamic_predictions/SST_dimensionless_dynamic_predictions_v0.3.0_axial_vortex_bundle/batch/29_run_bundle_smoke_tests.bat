@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
%PY_CMD% src\sst_axial_vortex_bundle.py campaign --config configs\bundle_smoke_physical.json --output outputs\bundle_smoke\physical
if errorlevel 1 goto :fail
%PY_CMD% src\sst_axial_vortex_bundle.py campaign --config configs\bundle_smoke_discretization.json --output outputs\bundle_smoke\discretization
if errorlevel 1 goto :fail
%PY_CMD% tools\analyze_bundle_modes.py --input outputs\bundle_smoke --output outputs\bundle_smoke\analysis
if errorlevel 1 goto :fail
start "" "%ROOT%\outputs\bundle_smoke"
pause
exit /b 0
:fail
echo [ERROR] Smoke tests faalden.
pause
exit /b 1
