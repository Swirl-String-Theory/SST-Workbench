@echo off
setlocal
cd /d "%~dp0"
set "PRESET=%~1"
if "%PRESET%"=="" set "PRESET=basic"
set "PYTHONPATH=%CD%\src;%CD%"
.venv\Scripts\python.exe -m sst_phase_delay_falsifier.cli backend --require-cpp || exit /b 1
.venv\Scripts\python.exe -m sst_phase_delay_falsifier.cli measure --blind blind_work --out results\nonlinear_measurements.json --config "configs\%PRESET%.json"
exit /b %ERRORLEVEL%
