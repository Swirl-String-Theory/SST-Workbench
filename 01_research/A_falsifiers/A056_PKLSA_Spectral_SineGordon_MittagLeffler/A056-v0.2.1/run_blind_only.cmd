@echo off
setlocal
cd /d "%~dp0"
set PRESET=%1
if "%PRESET%"=="" set PRESET=basic
call run_install.cmd || exit /b 1
call run_02_backend_selftest.cmd || exit /b 1
call run_10_framework_selftest.cmd || exit /b 1
.venv\Scripts\python.exe -m a056_falsifier.pipeline --input data\synthetic_blind --config configs\%PRESET%.json || exit /b 1
call run_40_report.cmd || exit /b 1
