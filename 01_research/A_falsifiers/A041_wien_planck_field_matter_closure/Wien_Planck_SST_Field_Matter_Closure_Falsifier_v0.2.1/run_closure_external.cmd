@echo off
setlocal
if "%~1"=="" (
  echo Usage: run_closure_external.cmd observations.csv
  exit /b 2
)
call .venv\Scripts\activate.bat || exit /b 1
python -m sst_wp.closure_analyze "%~1" --config config\basic.json --out outputs\closure_external.json || exit /b 1
endlocal
