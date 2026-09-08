@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
echo ============================================================
echo SST Explicit Closed Vortex-Thread Blind Falsifier v0.3.0
echo PRIOR-RELEASE HOLDOUT certification
echo Dataset: %DATASET%
echo ============================================================
call run_install.cmd
if errorlevel 1 goto :fail
call run_build_native.cmd
if errorlevel 1 goto :fail
call run_selftest.cmd
if errorlevel 1 goto :fail
call run_holdout_certification.cmd "%DATASET%"
if errorlevel 1 goto :fail
echo PASS - holdout certification completed.
exit /b 0
:fail
echo FAIL - holdout certification stopped with errorlevel %errorlevel%
exit /b %errorlevel%
