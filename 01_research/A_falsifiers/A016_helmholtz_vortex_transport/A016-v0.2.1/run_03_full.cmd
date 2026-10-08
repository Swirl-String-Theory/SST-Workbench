@echo off
cd /d "%~dp0"
call run_all.cmd FULL
exit /b %ERRORLEVEL%
