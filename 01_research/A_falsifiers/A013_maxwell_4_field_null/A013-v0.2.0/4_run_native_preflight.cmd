@echo off
call "%~dp0run_native_preflight.cmd" %*
exit /b %ERRORLEVEL%
