@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo ERROR: run run_all.cmd first.
  exit /b 3
)
if not exist outputs mkdir outputs
REM Usage:
REM   run_dataset_inventory.cmd
REM   run_dataset_inventory.cmd [output-json]
REM   run_dataset_inventory.cmd ^<dataset-folder^> [output-json]
REM Default root = Knot_Library/Sources
if "%~1"=="" (
  .venv\Scripts\python.exe -m sst_knotlib scan-dataset --out outputs\dataset_inventory.json
  exit /b %errorlevel%
)
if exist "%~1\" (
  set "OUT=%~2"
  if "%OUT%"=="" set "OUT=outputs\dataset_inventory.json"
  .venv\Scripts\python.exe -m sst_knotlib scan-dataset "%~1" --out "%OUT%"
  exit /b %errorlevel%
)
.venv\Scripts\python.exe -m sst_knotlib scan-dataset --out "%~1"
exit /b %errorlevel%
