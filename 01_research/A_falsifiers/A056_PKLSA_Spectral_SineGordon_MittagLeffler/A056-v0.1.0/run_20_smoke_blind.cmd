@echo off
setlocal
set PRESET=%1
if "%PRESET%"=="" set PRESET=basic
call .venv\Scripts\activate.bat || exit /b 1
python tools\generate_smoke_data.py || exit /b 1
python -m a056_falsifier.pipeline --input data\blind --config configs\%PRESET%.json || exit /b 1
