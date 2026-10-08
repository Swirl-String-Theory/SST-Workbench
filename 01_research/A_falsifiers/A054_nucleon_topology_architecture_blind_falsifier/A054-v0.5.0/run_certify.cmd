@echo off
call "%~dp0run_all.cmd" CERTIFY %*
exit /b %ERRORLEVEL%
