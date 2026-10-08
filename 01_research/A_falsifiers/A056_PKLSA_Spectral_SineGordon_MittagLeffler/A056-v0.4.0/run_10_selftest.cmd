@echo off
setlocal
cd /d "%~dp0"
call run_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd -m pytest tests -q
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd run_instance.py SELFTEST
exit /b %ERRORLEVEL%
