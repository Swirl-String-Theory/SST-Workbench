@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set "OUT=%~2"
if "%OUT%"=="" set "OUT=..\..\KnotPlot\qhp_extended"
echo ============================================================
echo SST KnotPlot QHP Sweep Generator v0.1.1
echo EXTENDED axis sweep
echo Seeds: %DATASET%
echo Output: %OUT%
echo ============================================================
call run_setup.cmd
if errorlevel 1 goto :fail
call run_selftest.cmd
if errorlevel 1 goto :fail
call run_extended.cmd "%DATASET%" "%OUT%"
if errorlevel 1 goto :fail
exit /b 0
:fail
exit /b 1
