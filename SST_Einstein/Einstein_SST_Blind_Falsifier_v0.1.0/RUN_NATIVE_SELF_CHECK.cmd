@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call "%~dp0run_00_install.cmd" || exit /b 1
call "%~dp0run_01_check_backend.cmd"
exit /b %errorlevel%
