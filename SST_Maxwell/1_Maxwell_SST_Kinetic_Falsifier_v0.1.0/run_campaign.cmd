@echo off
setlocal
if "%~1"=="" (
  echo Usage: run_campaign.cmd ^<config.json^> ^<output-directory^>
  exit /b 2
)
if "%~2"=="" (
  echo Usage: run_campaign.cmd ^<config.json^> ^<output-directory^>
  exit /b 2
)
set PYTHONPATH=%~dp0src
python -m maxwell_sst_falsifier run --config "%~1" --out "%~2"
endlocal
