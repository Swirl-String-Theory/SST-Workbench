@echo off
setlocal
call _common.cmd
if not exist .venv py -3 -m venv .venv || exit /b 1
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel || exit /b 1
python -m pip install -r requirements.txt || exit /b 1
python -m pip install -e . || exit /b 1
