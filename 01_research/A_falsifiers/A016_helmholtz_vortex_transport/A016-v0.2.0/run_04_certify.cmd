@echo off
cd /d "%~dp0"
call run_all.cmd CERTIFY
exit /b %ERRORLEVEL%
