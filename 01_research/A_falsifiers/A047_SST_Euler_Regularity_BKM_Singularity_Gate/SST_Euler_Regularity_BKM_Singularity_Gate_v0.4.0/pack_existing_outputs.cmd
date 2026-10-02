@echo off
setlocal
cd /d "%~dp0"
if not exist .venv call run_00_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
python tools_pack_existing_outputs.py
