@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
if "%~1"=="" (
  echo Usage: run_closure_external.cmd observations.csv
  exit /b 2
)
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
"%PY%" -m sst_wp.closure_analyze "%~1" --config config\basic.json --out outputs\closure_external.json || exit /b 1
popd
endlocal
