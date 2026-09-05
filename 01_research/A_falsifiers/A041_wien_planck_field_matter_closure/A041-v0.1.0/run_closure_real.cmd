@echo off
setlocal
if "%~1"=="" (
  echo Usage: run_closure_real.cmd closure_observations.csv
  exit /b 2
)
set PYTHONPATH=%~dp0src
if not exist outputs mkdir outputs
py -3 -m sst_wp.closure_analyze "%~1" config\default.json outputs\closure_real.json
endlocal
