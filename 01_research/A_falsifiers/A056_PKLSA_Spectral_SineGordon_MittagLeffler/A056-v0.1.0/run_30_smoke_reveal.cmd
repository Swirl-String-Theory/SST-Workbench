@echo off
setlocal
call .venv\Scripts\activate.bat || exit /b 1
python tools\reveal_smoke.py || exit /b 1
