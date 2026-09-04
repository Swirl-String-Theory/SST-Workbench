@echo off
setlocal
cd /d "%~dp0"
call "cmd\_ENSURE_NATIVE.cmd"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe run_blind_convergence.py --output results\blind_convergence
exit /b %errorlevel%
