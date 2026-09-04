@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_all_normal.cmd
exit /b %ERRORLEVEL%
