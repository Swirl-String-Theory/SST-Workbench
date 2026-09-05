@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_00_install.cmd
if errorlevel 1 exit /b %errorlevel%
call run_01_basic.cmd
if errorlevel 1 exit /b %errorlevel%
call run_02_extended.cmd
exit /b %ERRORLEVEL%
