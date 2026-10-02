@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
echo ============================================================
echo SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.1.0
echo BASIC one-click chain
echo Dataset: %DATA%
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call run_basic.cmd "%DATA%" || exit /b 1
