@echo off
setlocal
cd /d "%~dp0\..\.."
call "cmd\_ENSURE_NATIVE.cmd"
if errorlevel 1 exit /b 1
set SST_HOPF_FORCE_PYTHON=0
if not exist results\manual\step04\hopf_charge_fields.npz call "cmd\steps\04_H1_H3_HOPF_CHARGE.cmd"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe 05_heliciteitsbridge.py results\manual\step04\hopf_charge_fields.npz --output results\manual\step05
exit /b %errorlevel%
