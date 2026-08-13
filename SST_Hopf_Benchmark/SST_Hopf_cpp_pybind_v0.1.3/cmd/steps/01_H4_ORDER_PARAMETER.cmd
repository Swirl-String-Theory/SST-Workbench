@echo off
setlocal
cd /d "%~dp0\..\.."
call "cmd\_ENSURE_NATIVE.cmd"
if errorlevel 1 exit /b 1
set SST_HOPF_FORCE_PYTHON=0
.venv\Scripts\python.exe 01_definieer_sst_orderparameter.py --output results\manual\step01 --n 48
exit /b %errorlevel%
