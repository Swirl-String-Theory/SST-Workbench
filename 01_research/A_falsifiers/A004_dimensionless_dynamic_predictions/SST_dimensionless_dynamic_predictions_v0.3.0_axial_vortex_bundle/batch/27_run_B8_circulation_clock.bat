@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
set OUT=%ROOT%\outputs\B8_circulation_clock
echo === B8 CIRCULATIEFASE ALS KLOKDRAGER ===
%PY_CMD% src\sst_axial_vortex_bundle.py campaign --config configs\B8_circulation_clock.json --output "%OUT%"
if errorlevel 1 goto :fail
start "" "%OUT%"
pause
exit /b 0
:fail
echo [ERROR] B8 faalde.
pause
exit /b 1
