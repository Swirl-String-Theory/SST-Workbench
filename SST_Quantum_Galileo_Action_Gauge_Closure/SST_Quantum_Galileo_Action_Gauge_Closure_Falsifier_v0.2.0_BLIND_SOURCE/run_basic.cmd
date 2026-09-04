@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%
if not exist "SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.2.0-outputs\blind\public_manifest.json" (
  call run_prepare_blind.cmd
  if errorlevel 1 exit /b 1
)
python -m sst_qgi.cli basic --config configs\basic.json
if errorlevel 1 exit /b 1
endlocal
