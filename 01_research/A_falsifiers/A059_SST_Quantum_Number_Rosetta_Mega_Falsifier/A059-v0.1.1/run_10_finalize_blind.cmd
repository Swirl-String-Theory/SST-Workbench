@echo off
setlocal
call run_python.cmd run_instance.py FULL
exit /b %ERRORLEVEL%
