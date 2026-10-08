@echo off
setlocal
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=SMOKE"
call run_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd -m pytest tests -q
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd run_instance.py SELFTEST
if errorlevel 1 exit /b %ERRORLEVEL%
if /I "%MODE%"=="SMOKE" goto SMOKE
call run_python.cmd run_instance.py %MODE%
exit /b %ERRORLEVEL%
:SMOKE
set "A056_CONFIG=configs\framework_smoke.json"
call run_python.cmd run_instance.py FULL
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd run_instance.py REVEAL_IF_ALLOWED
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd private\validate_smoke_reveal.py
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd tools\package_outputs.py
exit /b %ERRORLEVEL%
