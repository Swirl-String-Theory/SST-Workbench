@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe call run_00_install.cmd
set OUT=%CD%\A054_Low_Crossing_Topology_Discovery_v0.3.0-outputs
if exist "%OUT%" rmdir /s /q "%OUT%"
.venv\Scripts\python.exe -m a054_ntaf.cli prepare-v030 --output "%OUT%" --package-root "%CD%" --n 144 || exit /b 1
.venv\Scripts\python.exe tools\assert_full_prepare.py "%OUT%" || exit /b 1
.venv\Scripts\python.exe tools\build_blind_runner.py --campaign "%OUT%" || exit /b 1
set PYTHONPATH=%OUT%\blind_runner
.venv\Scripts\python.exe "%OUT%\blind_runner\run_blind.py" --campaign "%OUT%" --config "%CD%\configs\discovery_basic.json" || exit /b 1
.venv\Scripts\python.exe tools\pack_outputs.py --campaign "%OUT%" --mode blind
endlocal
