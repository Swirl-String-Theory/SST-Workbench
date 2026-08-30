@echo off
setlocal
set OUT=%~1
if "%OUT%"=="" set OUT=outputs\basic
call .venv\Scripts\activate.bat
python -m sst_modal_clock.cli reveal "%OUT%"
