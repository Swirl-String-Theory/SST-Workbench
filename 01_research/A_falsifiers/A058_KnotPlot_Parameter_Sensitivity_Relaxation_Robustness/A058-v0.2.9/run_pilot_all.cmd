@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_all.cmd BASIC "%~1"
exit /b %ERRORLEVEL%
