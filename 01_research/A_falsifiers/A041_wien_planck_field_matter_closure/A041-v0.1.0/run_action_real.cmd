@echo off
setlocal
if "%~1"=="" (
  echo Usage: run_action_real.cmd observations.csv
  exit /b 2
)
set PYTHONPATH=%~dp0src
if not exist outputs mkdir outputs
py -3 -m sst_wp.action_prepare "%~1" outputs\action_real_blind.csv outputs\action_real_key.json || exit /b 1
py -3 -m sst_wp.action_analyze outputs\action_real_blind.csv config\default.json outputs\action_real_blind_analysis.json || exit /b 1
echo Blind analysis complete. Inspect outputs\action_real_blind_analysis.json before reveal.
echo To reveal, run: run_action_reveal.cmd
endlocal
