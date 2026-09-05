@echo off
setlocal
cd /d "%~dp0"
if not defined OMP_NUM_THREADS set "OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%"
if not exist ".venv\Scripts\python.exe" (echo [SST] .venv missing. Run run_install.cmd first.& exit /b 1)
echo ============================================================
echo [SST] Unit tests + synthetic closed-loop controls
echo ============================================================
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m einstein_sst_gates.cli selftest --config config\basic.json --out outputs\selftest
if errorlevel 1 exit /b 1
