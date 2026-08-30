@echo off
setlocal
call _common.cmd
call .venv\Scripts\activate.bat
python setup_native.py build_ext --inplace || exit /b 1
