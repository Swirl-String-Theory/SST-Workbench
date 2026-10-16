\
@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
python setup_native.py build_ext --inplace
if errorlevel 1 exit /b 1
python -m pytest -q
if errorlevel 1 exit /b 1
call run_install_export_test.cmd
exit /b %ERRORLEVEL%
