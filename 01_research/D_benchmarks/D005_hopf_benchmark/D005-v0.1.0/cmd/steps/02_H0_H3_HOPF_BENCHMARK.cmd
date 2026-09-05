@echo off
setlocal
cd /d "%~dp0\..\.."
call "cmd\_ENSURE_NATIVE.cmd"
if errorlevel 1 exit /b 1
set SST_HOPF_FORCE_PYTHON=0
.venv\Scripts\python.exe 02_analytische_hopf_benchmark.py --output results\manual\step02 --resolutions 24 32 48 64
exit /b %errorlevel%
