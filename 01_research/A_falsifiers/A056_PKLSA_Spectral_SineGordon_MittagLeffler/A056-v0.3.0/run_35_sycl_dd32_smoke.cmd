@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
%PY% tools\run_framework_dd32.py
exit /b %ERRORLEVEL%
