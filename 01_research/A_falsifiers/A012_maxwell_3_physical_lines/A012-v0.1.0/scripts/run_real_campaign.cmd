@echo off
REM Usage: run_real_campaign.cmd CAMPAIGN_CSV REDUCED_MOMENTUM_CSV OUTDIR [STORAGE_NPZ]
setlocal
cd /d "%~dp0\.."
set PYTHONPATH=%CD%\src;%PYTHONPATH%
if "%~3"=="" (
  echo Usage: %~nx0 CAMPAIGN_CSV REDUCED_MOMENTUM_CSV OUTDIR [STORAGE_NPZ]
  exit /b 2
)
set STORAGE=
if not "%~4"=="" set STORAGE=--storage "%~4"
py -m sst_maxwell_blind.cli run --config config\preregister.json --campaign "%~1" --reduced-momentum "%~2" %STORAGE% --outdir "%~3"
