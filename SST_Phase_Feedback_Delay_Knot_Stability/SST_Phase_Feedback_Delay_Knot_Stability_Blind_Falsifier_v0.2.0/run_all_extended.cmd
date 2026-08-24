@echo off
call "%~dp0run_all.cmd" "%~1" extended
exit /b %ERRORLEVEL%
