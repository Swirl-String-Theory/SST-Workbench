@echo off
call "%~dp0run_all.cmd" FREEZE "%~1"
exit /b %ERRORLEVEL%
