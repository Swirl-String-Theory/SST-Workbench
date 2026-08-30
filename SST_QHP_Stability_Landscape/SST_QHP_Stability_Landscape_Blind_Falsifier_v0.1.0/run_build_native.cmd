@echo off
setlocal
call .venv\Scripts\activate.bat
python setup_native.py build_ext --inplace
if errorlevel 1 exit /b 1
