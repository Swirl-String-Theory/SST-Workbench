@echo off
setlocal
set PYTHONPATH=%~dp0src
if not exist outputs mkdir outputs
if not exist demo mkdir demo
py -3 -m sst_wp.synthetic_controls action-negative demo\action_negative.csv
py -3 -m sst_wp.action_prepare demo\action_negative.csv outputs\action_negative_blind.csv outputs\action_negative_key.json
py -3 -m sst_wp.action_analyze outputs\action_negative_blind.csv config\default.json outputs\action_negative_analysis.json
py -3 -m sst_wp.action_reveal outputs\action_negative_analysis.json outputs\action_negative_key.json config\default.json outputs\action_negative_reveal.json
endlocal
