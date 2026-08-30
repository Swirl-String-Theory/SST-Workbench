@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
set "OUT=%~2"
if "%OUT%"=="" set "OUT=..\..\KnotPlot\qhp"
echo ============================================================
echo SST KnotPlot QHP Sweep Generator v0.1.1
echo BASIC one-click chain
echo Seeds: %DATASET%
echo Output: %OUT%
echo ============================================================
call run_setup.cmd
if errorlevel 1 goto :fail
call run_selftest.cmd
if errorlevel 1 goto :fail
call run_basic.cmd "%DATASET%" "%OUT%"
if errorlevel 1 goto :fail
echo.
echo PASS - QHP dataset generated at %OUT%
exit /b 0
:fail
echo.
echo FAILED
exit /b 1
