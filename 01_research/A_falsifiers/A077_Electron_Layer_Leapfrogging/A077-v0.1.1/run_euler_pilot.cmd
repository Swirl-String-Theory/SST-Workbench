@echo off
setlocal
cd /d "%~dp0"
if defined SST_PYTHON (set "PY=%SST_PYTHON%") else if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
"%PY%" -m science.euler_field --config configs/euler_pilot.json --output A077_euler_pilot_v0.1.1-outputs
exit /b %ERRORLEVEL%
