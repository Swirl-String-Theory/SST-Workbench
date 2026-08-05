@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
set OUT=%ROOT%\outputs\C9_iso_gamma_area_discretization
if not exist "%OUT%" mkdir "%OUT%"

%PY_CMD% src\sst_iso_gamma_area_clock.py campaign ^
  --config configs\C9_iso_gamma_area_discretization.json ^
  --output "%OUT%"
if errorlevel 1 goto :fail

%PY_CMD% tools\analyze_iso_gamma_area.py ^
  --input "%OUT%" ^
  --output "%OUT%\analysis"
if errorlevel 1 goto :fail

start "" "%OUT%\analysis"
pause
exit /b 0
:fail
echo [ERROR] C9 discretization check faalde.
pause
exit /b 1
