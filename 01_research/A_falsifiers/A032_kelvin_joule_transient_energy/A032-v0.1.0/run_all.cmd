@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set "BACKEND=%~2"
if "%BACKEND%"=="" set "BACKEND=auto"
call run_install.cmd
if errorlevel 1 exit /b 1
call run_smoke.cmd
if errorlevel 1 exit /b 1
call run_basic.cmd "%DATASET%" %BACKEND%
if errorlevel 1 exit /b 1
call run_extended.cmd "%DATASET%" %BACKEND%
exit /b %errorlevel%
