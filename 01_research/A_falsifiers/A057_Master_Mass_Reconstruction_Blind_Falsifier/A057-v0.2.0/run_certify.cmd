@echo off
call "%~dp0run_all.cmd" CERTIFY "%~1"
exit /b %ERRORLEVEL%
