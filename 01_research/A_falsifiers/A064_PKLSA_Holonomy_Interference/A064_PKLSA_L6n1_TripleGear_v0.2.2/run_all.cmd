@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -m pip install -q -r requirements.txt
if errorlevel 1 exit /b 1
if "%~1"=="" (
  .venv\Scripts\python.exe hopf_cli.py RUN
) else (
  .venv\Scripts\python.exe hopf_cli.py %*
)
exit /b %errorlevel%
