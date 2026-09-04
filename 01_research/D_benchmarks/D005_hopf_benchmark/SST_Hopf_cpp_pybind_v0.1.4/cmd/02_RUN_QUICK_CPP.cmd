@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
call ".venv\Scripts\activate.bat"
set SST_HOPF_FORCE_PYTHON=0
python run_all.py --tier quick --out-root results\quick_cpp
exit /b %errorlevel%
