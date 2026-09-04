@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
echo ============================================================
echo SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.2.0
echo BASIC staged one-click chain
echo Dataset: %DATA%
echo Stage A: T=24 mesh-stabilized recurrence
echo Stage B: material causal test only if Stage A passes
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call run_basic.cmd "%DATA%" || exit /b 1
