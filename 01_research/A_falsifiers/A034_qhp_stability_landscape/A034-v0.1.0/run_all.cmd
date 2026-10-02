@echo off
setlocal
set "DATASET=%~1"
if "%DATASET%"=="" set "DATASET=..\..\KnotPlot\qhp"
echo ============================================================
echo SST QHP Stability Landscape Blind Falsifier v0.1.2
echo BASIC one-click chain
echo Dataset: %DATASET%
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call run_basic.cmd "%DATASET%" outputs\basic || exit /b 1
echo DONE: outputs\basic
