@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_RIDGERUNNER_POLISH.bat "C:\path\to\trefoil_polish.txt"
  pause
  exit /b 1
)
py -3 -m pip install -e . --no-build-isolation
if errorlevel 1 goto :error
py -3 -m sstcbhf analyze --input "%~1" --samples 384 --hydro-samples 96 --hydro-interactions full nonlocal --thresholds-json configs\default_thresholds.json --out outputs\ridgerunner_3_1_contact_hydro
set RC=%ERRORLEVEL%
echo.
if %RC% EQU 0 (echo All configured gates passed.) else (echo One or more gates failed or remain unresolved.)
pause
exit /b %RC%
:error
echo Installation failed.
pause
exit /b 1
