@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_all.cmd REVEAL
exit /b %ERRORLEVEL%
