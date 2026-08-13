@echo off
setlocal
cd /d "%~dp0\..\.."
call "cmd\_ENSURE_NATIVE.cmd"
if errorlevel 1 exit /b 1
set SST_HOPF_FORCE_PYTHON=0
.venv\Scripts\python.exe 08_trefoil_integratie.py --output results\manual\step08
exit /b %errorlevel%
