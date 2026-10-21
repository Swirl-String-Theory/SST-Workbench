@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv || exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install -q -r requirements.txt || exit /b 1
python -m pip install -q -e . || exit /b 1
pytest -q || exit /b 1
python -m sst_cgtdlef.run || exit /b 1
python tools\audit_blind.py || exit /b 1
endlocal
