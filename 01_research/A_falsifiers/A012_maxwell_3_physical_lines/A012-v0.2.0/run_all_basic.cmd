@echo off
setlocal
call "%~dp0run_00_install.cmd"
if errorlevel 1 exit /b %errorlevel%
call "%~dp0run_01_preflight.cmd"
if errorlevel 1 exit /b %errorlevel%
call "%~dp0run_02_basic.cmd"
exit /b %errorlevel%
