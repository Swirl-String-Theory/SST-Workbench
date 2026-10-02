@echo off
setlocal
cd /d "%~dp0"
if not exist .venv py -3 -m venv .venv || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
python -m pip install -r requirements.txt || exit /b 1
python -m pip install -e . --no-build-isolation || exit /b 1
python tests\test_smoke.py
