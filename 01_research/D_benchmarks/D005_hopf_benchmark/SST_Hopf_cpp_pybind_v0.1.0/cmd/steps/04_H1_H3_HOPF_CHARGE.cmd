@echo off
setlocal
cd /d "%~dp0\..\.."
call "cmd\_ENSURE_NATIVE.cmd"
if errorlevel 1 exit /b 1
set SST_HOPF_FORCE_PYTHON=0
if not exist results\manual\step02\analytic_hopf_benchmark.npz call "cmd\steps\02_H0_H3_HOPF_BENCHMARK.cmd"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe 04_hopf_lading_numeriek.py results\manual\step02\analytic_hopf_benchmark.npz --output results\manual\step04
exit /b %errorlevel%
