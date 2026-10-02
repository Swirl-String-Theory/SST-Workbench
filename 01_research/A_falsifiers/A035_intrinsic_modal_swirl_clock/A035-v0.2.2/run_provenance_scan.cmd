@echo off
setlocal
call .venv\Scripts\activate.bat || exit /b 1
if not exist outputs mkdir outputs
python -m sst_modal_clock.cli scan-provenance config\basic.json > outputs\SOURCE_SCAN.json || exit /b 1
type outputs\SOURCE_SCAN.json
