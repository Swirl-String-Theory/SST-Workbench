@echo off
setlocal
call "%~dp0run_00_install.cmd"
if errorlevel 1 exit /b %errorlevel%
call "%~dp0run_01_preflight.cmd" certification
if errorlevel 1 exit /b %errorlevel%
call "%~dp0run_03_certification.cmd"
exit /b %errorlevel%
