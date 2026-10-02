@echo off
setlocal
set "WORK=%~1"
if "%WORK%"=="" set "WORK=outputs\basic"
set OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%
call .venv\Scripts\activate.bat
python -m sst_bsrp_falsifier.cli run "%WORK%" config\basic.json
if errorlevel 1 exit /b 1
python -m sst_bsrp_falsifier.cli analyze "%WORK%" config\basic.json
