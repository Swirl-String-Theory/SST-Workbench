@echo off
setlocal
set PYTHONPATH=%~dp0src
if not exist outputs mkdir outputs
if not exist demo mkdir demo
py -3 -m sst_wp.synthetic_controls action-positive demo\action_positive.csv
py -3 -m sst_wp.action_prepare demo\action_positive.csv outputs\action_blind.csv outputs\action_key.json
py -3 -m sst_wp.action_analyze outputs\action_blind.csv config\default.json outputs\action_blind_analysis.json
py -3 -m sst_wp.action_reveal outputs\action_blind_analysis.json outputs\action_key.json config\default.json outputs\action_reveal.json
echo.
echo Synthetic positive control complete. This is pipeline validation, not SST evidence.
endlocal
