@echo off
setlocal
cd /d "%~dp0"
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
echo ============================================================
echo SST Local Thread Texture + Boost Invariance Blind Falsifier
echo v0.1.0 - EXTENDED convergence chain
echo Dataset: %DATASET%
echo ============================================================
echo [1/4] Install / update environment
call run_install.cmd
if errorlevel 1 goto :fail
echo [2/4] Strict C++17/pybind11 native build
call run_build_native.cmd
if errorlevel 1 goto :fail
echo [3/4] Native-vs-Python parity and boost-null selftest
call run_selftest.cmd
if errorlevel 1 goto :fail
echo [4/4] Blind EXTENDED N-ladder campaign
call run_extended.cmd "%DATASET%"
if errorlevel 1 goto :fail
echo ============================================================
echo PASS - extended chain completed. Inspect outputs_extended_*.
echo ============================================================
exit /b 0
:fail
echo ============================================================
echo FAIL - extended chain stopped with errorlevel %errorlevel%
echo ============================================================
exit /b %errorlevel%
