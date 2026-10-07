@echo off
setlocal
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=SMOKE"
call run_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
set "PY=.venv\Scripts\python.exe"
%PY% -m pytest tests -q
if errorlevel 1 exit /b %ERRORLEVEL%
%PY% run_instance.py SELFTEST
if errorlevel 1 exit /b %ERRORLEVEL%
if /I "%MODE%"=="SMOKE" goto SMOKE
%PY% run_instance.py %MODE%
exit /b %ERRORLEVEL%
:SMOKE
%PY% run_instance.py FULL
if errorlevel 1 exit /b %ERRORLEVEL%
%PY% run_instance.py REVEAL
if errorlevel 1 exit /b %ERRORLEVEL%
%PY% private\validate_smoke_reveal.py
if errorlevel 1 exit /b %ERRORLEVEL%
%PY% tools\package_outputs.py
exit /b %ERRORLEVEL%
