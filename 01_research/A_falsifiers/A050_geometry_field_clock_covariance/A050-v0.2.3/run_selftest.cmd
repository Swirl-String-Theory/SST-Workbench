@echo off
call run_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat
python tools\preflight.py || exit /b 1
python -m pytest -q
