@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
"%PY%" -m sst_wp.inventory "%DATA%" --out outputs\dataset_inventory.json --n 96 || exit /b 1
popd
endlocal
