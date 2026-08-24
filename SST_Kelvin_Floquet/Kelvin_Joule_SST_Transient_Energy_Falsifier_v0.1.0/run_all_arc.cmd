@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
call run_arc.cmd
if errorlevel 1 exit /b 1
call run_arc_basic.cmd "%DATASET%"
if errorlevel 1 exit /b 1
call run_arc_extended.cmd "%DATASET%"
exit /b %errorlevel%
