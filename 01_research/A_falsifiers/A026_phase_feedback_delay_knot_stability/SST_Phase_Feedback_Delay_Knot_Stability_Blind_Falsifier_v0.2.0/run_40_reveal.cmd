@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src;%CD%"
if not exist private_reveal\reveal_key.json ( echo ERROR: reveal key missing. & exit /b 1 )
.venv\Scripts\python.exe -m sst_phase_delay_falsifier.cli reveal --eval results\BLIND_EVALUATION.json --key private_reveal\reveal_key.json --out results\REVEALED_EVALUATION.json || exit /b 1
.venv\Scripts\python.exe -m sst_phase_delay_falsifier.cli prep-audit --key private_reveal\reveal_key.json --out results\PREPARATION_AUDIT.json
exit /b %ERRORLEVEL%
