@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
call ".venv\Scripts\activate.bat"
set SST_HOPF_FORCE_PYTHON=1
python run_all.py --tier standard --force-python --out-root results\standard_python
exit /b %errorlevel%
