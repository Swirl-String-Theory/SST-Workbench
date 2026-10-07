@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
"%PY%" -m pytest -q tests || exit /b 1
"%PY%" tests\selftest.py || exit /b 1
"%PY%" tools\check_blind.py || exit /b 1
