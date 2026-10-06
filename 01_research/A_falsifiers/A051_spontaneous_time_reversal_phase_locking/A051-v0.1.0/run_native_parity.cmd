@echo off
setlocal
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python tools\native_parity.py
endlocal
