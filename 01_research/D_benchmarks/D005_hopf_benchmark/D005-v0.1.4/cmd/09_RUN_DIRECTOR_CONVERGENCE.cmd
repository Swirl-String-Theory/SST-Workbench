@echo off
setlocal
cd /d "%~dp0\.."
call "cmd\_ENSURE_NATIVE.cmd"
if errorlevel 1 exit /b 1
set SST_HOPF_FORCE_PYTHON=0
echo [SST-HOPF] Director/Hodge convergence: N=32,48,64,96,128
.venv\Scripts\python.exe run_director_convergence.py --output results\director_convergence --resolutions 32 48 64 96 128
exit /b %errorlevel%
