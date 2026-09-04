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
set OUT=%ROOT%\outputs\bundle_physical_tubes
echo === FYSIEKE BUIZEN ===
echo Gamma per buis blijft vast; totale circulatie groeit met N.
%PY_CMD% src\sst_axial_vortex_bundle.py campaign --config configs\B6_physical_tubes.json --output "%OUT%"
if errorlevel 1 goto :fail
start "" "%OUT%"
pause
exit /b 0
:fail
echo [ERROR] Fysieke-buizencampagne faalde.
pause
exit /b 1
