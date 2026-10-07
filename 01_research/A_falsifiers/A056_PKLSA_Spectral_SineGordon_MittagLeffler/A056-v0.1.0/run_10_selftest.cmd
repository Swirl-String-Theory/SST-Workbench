@echo off
setlocal
call .venv\Scripts\activate.bat || exit /b 1
python tests\selftest.py || exit /b 1
python tools\check_blind.py || exit /b 1
