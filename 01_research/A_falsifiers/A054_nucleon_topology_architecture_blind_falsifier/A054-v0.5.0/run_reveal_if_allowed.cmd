@echo off
call "%~dp0run_all.cmd" REVEAL_IF_ALLOWED %*
exit /b %ERRORLEVEL%
