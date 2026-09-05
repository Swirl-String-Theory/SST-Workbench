@echo off
setlocal
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -e .
