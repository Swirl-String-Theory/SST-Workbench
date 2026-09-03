@echo off
setlocal
call .venv\Scripts\activate.bat || exit /b 1
if not exist outputs mkdir outputs
python -m sst_wp.provenance outputs\provenance_audit.json || exit /b 1
endlocal
