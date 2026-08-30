@echo off
setlocal
set "WORK=%~1"
if "%WORK%"=="" set "WORK=outputs\extended"
set OMP_NUM_THREADS=%NUMBER_OF_PROCESSORS%
call .venv\Scripts\activate.bat
python -m sst_bsrp_falsifier.cli run "%WORK%" config\extended.json
if errorlevel 1 exit /b 1
python -m sst_bsrp_falsifier.cli analyze "%WORK%" config\extended.json
