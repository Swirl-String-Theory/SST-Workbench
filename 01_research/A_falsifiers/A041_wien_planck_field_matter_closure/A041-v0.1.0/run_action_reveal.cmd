@echo off
setlocal
set PYTHONPATH=%~dp0src
py -3 -m sst_wp.action_reveal outputs\action_real_blind_analysis.json outputs\action_real_key.json config\default.json outputs\action_real_reveal.json
endlocal
