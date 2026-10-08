@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_python.cmd run_instance.py FULL
exit /b %ERRORLEVEL%
