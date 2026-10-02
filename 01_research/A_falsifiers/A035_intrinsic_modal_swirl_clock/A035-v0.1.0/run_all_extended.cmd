@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
echo ============================================================
echo SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.1.0
echo EXTENDED one-click chain
echo Dataset: %DATA%
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call run_extended.cmd "%DATA%" || exit /b 1
call run_resolution.cmd "%DATA%" || exit /b 1
echo Resolution result: outputs\RESOLUTION_SUMMARY.json
