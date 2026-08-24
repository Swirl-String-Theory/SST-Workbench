@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
echo ============================================================
echo SST Explicit Closed Vortex-Thread Blind Falsifier v0.2.1
echo BASIC one-click chain
echo Dataset: %DATASET%
echo ============================================================
echo [1/5] Install / update environment
call run_install.cmd
if errorlevel 1 goto :fail
echo [2/5] Strict C++17/pybind11 native build
call run_build_native.cmd
if errorlevel 1 goto :fail
echo [3/5] Native-vs-Python + boost/closure selftest
call run_selftest.cmd
if errorlevel 1 goto :fail
echo [4/5] Blind BASIC nonlinear thread campaign
call run_basic.cmd "%DATASET%"
if errorlevel 1 goto :fail
echo [5/5] Complete - inspect newest outputs_basic_*\unblinded_report.json
echo ============================================================
echo PASS - execution and structural chain completed.
echo Bridge PASS/FAIL is scientific output; inspect the report.
echo ============================================================
exit /b 0
:fail
echo ============================================================
echo FAIL - chain stopped with errorlevel %errorlevel%
echo ============================================================
exit /b %errorlevel%
