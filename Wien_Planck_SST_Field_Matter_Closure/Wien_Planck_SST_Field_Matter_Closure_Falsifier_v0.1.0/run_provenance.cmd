@echo off
setlocal
set PYTHONPATH=%~dp0src
if not exist outputs mkdir outputs
py -3 -m sst_wp.provenance outputs\provenance_audit.json
endlocal
