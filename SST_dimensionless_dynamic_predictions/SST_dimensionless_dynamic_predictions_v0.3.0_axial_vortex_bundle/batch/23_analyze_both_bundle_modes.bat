@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
set OUT=%ROOT%\outputs\bundle_mode_analysis
if not exist "%OUT%" mkdir "%OUT%"
%PY_CMD% tools\analyze_bundle_modes.py --input outputs --output "%OUT%"
if errorlevel 1 goto :fail
start "" "%OUT%"
pause
exit /b 0
:fail
echo [ERROR] Analyse faalde.
pause
exit /b 1
