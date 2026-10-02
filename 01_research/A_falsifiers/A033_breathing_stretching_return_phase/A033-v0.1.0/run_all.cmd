@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\knots\final"
echo ============================================================
echo SST Breathing-Stretching-Return-Phase Causality Falsifier v0.1.1
echo BASIC blind one-click chain
echo Dataset: %DATASET%
echo ============================================================
echo [1/5] Environment
call run_setup.cmd || goto :fail
echo [2/5] Native C++17/pybind11/OpenMP build
call run_build_native.cmd || goto :fail
echo [3/5] Native-vs-Python selftest
call run_selftest.cmd || goto :fail
echo [4/5] Blind prepare + campaign
call run_prepare.cmd "%DATASET%" outputs\basic config\basic.json || goto :fail
call run_basic.cmd outputs\basic || goto :fail
echo [5/5] Blind score complete. Reveal is deliberately separate.
echo Run: run_reveal.cmd outputs\basic
echo PASS: chain completed
exit /b 0
:fail
echo FAIL: errorlevel %errorlevel%
exit /b 1
