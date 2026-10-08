@echo off
cd /d "%~dp0"
call run_all.cmd SETUP
exit /b %ERRORLEVEL%
