@echo off
setlocal
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%
python setup.py build_ext --inplace
if errorlevel 1 exit /b %errorlevel%
