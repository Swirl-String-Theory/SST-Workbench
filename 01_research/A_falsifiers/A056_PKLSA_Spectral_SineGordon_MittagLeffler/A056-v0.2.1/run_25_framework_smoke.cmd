@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe call run_install.cmd || exit /b 1
.venv\Scripts\python.exe -m a056_falsifier.pipeline --input data\synthetic_blind --config configs\framework_smoke.json || exit /b 1
.venv\Scripts\python.exe tools\generate_report.py || exit /b 1
