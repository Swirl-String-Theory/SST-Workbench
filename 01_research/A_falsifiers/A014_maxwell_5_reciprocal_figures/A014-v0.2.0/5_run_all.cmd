@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call 5_run_install.cmd
if errorlevel 1 exit /b %errorlevel%
call 5_run_basic.cmd %*
if errorlevel 1 exit /b %errorlevel%
call 5_run_extended.cmd %*
exit /b %errorlevel%
