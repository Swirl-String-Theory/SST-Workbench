@echo off
setlocal
cd /d "%~dp0"
call run_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd tools\run_framework_dd32.py
exit /b %ERRORLEVEL%
