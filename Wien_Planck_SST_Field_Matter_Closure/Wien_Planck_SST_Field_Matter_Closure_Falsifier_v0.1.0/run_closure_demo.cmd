@echo off
setlocal
set PYTHONPATH=%~dp0src
if not exist outputs mkdir outputs
if not exist demo mkdir demo
py -3 -m sst_wp.synthetic_controls closure-positive demo\closure_positive.csv
py -3 -m sst_wp.closure_analyze demo\closure_positive.csv config\default.json outputs\closure_positive.json
py -3 -m sst_wp.synthetic_controls closure-negative demo\closure_negative.csv
py -3 -m sst_wp.closure_analyze demo\closure_negative.csv config\default.json outputs\closure_negative.json
endlocal
