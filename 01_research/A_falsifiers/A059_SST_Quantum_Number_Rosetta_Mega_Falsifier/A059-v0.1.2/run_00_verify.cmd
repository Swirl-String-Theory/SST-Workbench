@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_all.cmd VERIFY
exit /b %ERRORLEVEL%
