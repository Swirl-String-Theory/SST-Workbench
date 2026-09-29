@echo off
setlocal
call .venv\Scripts\activate.bat
python setup.py build_ext --inplace
endlocal
