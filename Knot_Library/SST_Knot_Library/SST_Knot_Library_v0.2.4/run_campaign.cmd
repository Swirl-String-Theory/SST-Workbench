@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_campaign.cmd ^<config.json^> ^<outdir^>
  exit /b 2
)
if "%~2"=="" (
  echo Usage: run_campaign.cmd ^<config.json^> ^<outdir^>
  exit /b 2
)
call .venv\Scripts\activate.bat || exit /b 1
python -m sst_knotlib campaign "%~1" --outdir "%~2"
