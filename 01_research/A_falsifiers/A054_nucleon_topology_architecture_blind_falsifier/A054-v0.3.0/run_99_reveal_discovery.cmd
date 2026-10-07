@echo off
setlocal
cd /d "%~dp0"
set OUT=%CD%\A054_Low_Crossing_Topology_Discovery_v0.3.0-outputs
if not exist "%OUT%\BLIND_SEAL.json" exit /b 2
.venv\Scripts\python.exe -m a054_ntaf.cli reveal-v030 --campaign "%OUT%" || exit /b 1
.venv\Scripts\python.exe tools\pack_outputs.py --campaign "%OUT%" --mode revealed
endlocal
