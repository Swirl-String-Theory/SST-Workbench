@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_dataset_inventory.cmd ^<dataset-folder^> [output-json]
  echo Example: run_dataset_inventory.cmd ..\..\KnotPlot\knots\final
  exit /b 2
)
set "OUT=%~2"
if "%OUT%"=="" set "OUT=outputs\dataset_inventory.json"
if not exist outputs mkdir outputs
if not exist .venv\Scripts\python.exe (
  echo ERROR: run run_all.cmd first.
  exit /b 3
)
.venv\Scripts\python.exe -m sst_knotlib scan-dataset "%~1" --out "%OUT%"
exit /b %errorlevel%
