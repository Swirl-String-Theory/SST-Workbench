@echo off
call .venv\Scripts\activate.bat
python tools\preflight.py || exit /b 1
python -m pytest -q
