@echo off
setlocal
set "WORK=%~1"
if "%WORK%"=="" set "WORK=outputs\basic"
call .venv\Scripts\activate.bat
python -m sst_bsrp_falsifier.cli reveal "%WORK%"
