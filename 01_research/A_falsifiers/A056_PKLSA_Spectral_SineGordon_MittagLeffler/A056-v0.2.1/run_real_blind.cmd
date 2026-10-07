@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_real_blind.cmd ^<dynamic-provider-dir^> [basic^|full]
  exit /b 2
)
set "PROVIDER=%~1"
set "PRESET=%~2"
if "%PRESET%"=="" set PRESET=full
call run_install.cmd || exit /b 1
call run_02_backend_selftest.cmd || exit /b 1
call run_10_framework_selftest.cmd || exit /b 1
if exist data\real_blind rmdir /s /q data\real_blind
.venv\Scripts\python.exe tools\ingest_pklsa_dynamic_provider.py "%PROVIDER%" data\real_blind || exit /b 1
.venv\Scripts\python.exe -m a056_falsifier.pipeline --input data\real_blind --config configs\%PRESET%.json || exit /b 1
call run_40_report.cmd || exit /b 1
