@echo off
setlocal
if "%~1"=="" (echo Usage: run_real_blind.cmd INPUT_DIR [basic^|full] & exit /b 2)
set INPUT=%~1
set PRESET=%~2
if "%PRESET%"=="" set PRESET=basic
call .venv\Scripts\activate.bat || exit /b 1
python tools\check_blind.py || exit /b 1
python -m a056_falsifier.pipeline --input "%INPUT%" --config configs\%PRESET%.json || exit /b 1
