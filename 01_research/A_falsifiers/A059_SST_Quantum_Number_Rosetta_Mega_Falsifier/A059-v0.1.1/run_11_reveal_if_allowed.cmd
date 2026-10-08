@echo off
setlocal
call run_python.cmd run_instance.py REVEAL_IF_ALLOWED
exit /b %ERRORLEVEL%
