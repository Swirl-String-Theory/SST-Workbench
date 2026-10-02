@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_dataset_certify.cmd ^<dataset-folder^> [output-json]
  echo Requires an optional space-curve provider such as pyknotid for CERTIFIED results.
  exit /b 2
)
set "OUT=%~2"
if "%OUT%"=="" set "OUT=outputs\dataset_inventory_certified.json"
if not exist outputs mkdir outputs
if not exist .venv\Scripts\python.exe (
  echo ERROR: run run_all.cmd first.
  exit /b 3
)
.venv\Scripts\python.exe -m sst_knotlib scan-dataset "%~1" --certify --provider auto --out "%OUT%"
exit /b %errorlevel%
