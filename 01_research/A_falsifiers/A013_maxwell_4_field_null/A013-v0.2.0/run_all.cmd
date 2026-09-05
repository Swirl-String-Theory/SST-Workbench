@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "KNOT_DIR=%~1"
call run_install.cmd
if errorlevel 1 exit /b %errorlevel%
call run_native_preflight.cmd
if errorlevel 1 exit /b %errorlevel%
call run_basic.cmd "%KNOT_DIR%"
if errorlevel 1 exit /b %errorlevel%
call run_extended.cmd "%KNOT_DIR%"
exit /b %ERRORLEVEL%
