@echo off
setlocal
set PYTHONPATH=%~dp0src
python -m maxwell_sst_falsifier run --config "%~dp0examples\synthetic_fail\config.json" --out "%~dp0outputs\synthetic_fail"
endlocal
