@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
echo ============================================================
echo SST Explicit Closed Vortex-Thread Blind Falsifier v0.2.2
echo HIGHRES fixed-core N=256/512/1024 chain
echo Dataset: %DATASET%
echo ============================================================
call run_install.cmd
if errorlevel 1 goto :fail
call run_build_native.cmd
if errorlevel 1 goto :fail
call run_selftest.cmd
if errorlevel 1 goto :fail
call run_highres.cmd "%DATASET%"
if errorlevel 1 goto :fail
echo PASS - high-resolution chain completed.
exit /b 0
:fail
echo FAIL - high-resolution chain stopped with errorlevel %errorlevel%
exit /b %errorlevel%
