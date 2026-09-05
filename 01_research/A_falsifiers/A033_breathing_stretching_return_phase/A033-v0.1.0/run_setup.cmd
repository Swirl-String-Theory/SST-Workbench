@echo off
setlocal
if not exist .venv py -3 -m venv .venv 2>nul
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -e .
if errorlevel 1 exit /b 1
