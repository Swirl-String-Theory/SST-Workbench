@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install pybind11 setuptools wheel
python setup.py build_ext --inplace
endlocal
