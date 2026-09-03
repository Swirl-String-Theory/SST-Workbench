@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_dataset_inventory.cmd ^<dataset-folder^> [output-json]
  echo Example: run_dataset_inventory.cmd ..\..\KnotPlot\knots\final
  exit /b 2
)
if not exist outputs mkdir outputs
if not exist outputs\dataset_inventories mkdir outputs\dataset_inventories
if not exist .venv\Scripts\python.exe (
  echo ERROR: run run_all.cmd first.
  exit /b 3
)
set "OUT=%~2"
if "%OUT%"=="" (
  set "SST_SCAN_ROOT=%~1"
  for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$r=(Resolve-Path -LiteralPath $env:SST_SCAN_ROOT).Path; $leaf=Split-Path -Leaf $r; if([string]::IsNullOrWhiteSpace($leaf)){$leaf='root'}; $safe=$leaf -replace '[^A-Za-z0-9_.-]','_'; $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'; Write-Output ('outputs\dataset_inventories\'+$safe+'_'+$stamp+'.json')"`) do set "OUT=%%I"
)
.venv\Scripts\python.exe -m sst_knotlib scan-dataset "%~1" --out "%OUT%"
if errorlevel 1 exit /b %errorlevel%
copy /y "%OUT%" outputs\dataset_inventory.json >nul
 echo Saved: %OUT%
 echo Latest: outputs\dataset_inventory.json
exit /b 0
