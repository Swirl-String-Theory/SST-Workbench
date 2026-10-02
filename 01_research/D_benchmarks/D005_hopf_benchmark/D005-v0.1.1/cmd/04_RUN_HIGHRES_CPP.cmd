@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
call ".venv\Scripts\activate.bat"
set SST_HOPF_FORCE_PYTHON=0
echo [SST-HOPF] HIGH uses N up to 128 and may require several GB RAM.
python run_all.py --tier high --out-root results\high_cpp
exit /b %errorlevel%
