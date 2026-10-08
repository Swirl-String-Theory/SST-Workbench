@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
%PY% -m pytest tests -q
if errorlevel 1 exit /b %ERRORLEVEL%
%PY% run_instance.py SELFTEST
exit /b %ERRORLEVEL%
