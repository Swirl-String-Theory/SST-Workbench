@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
call run_00_setup.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_02_selftest.cmd || exit /b 1
call run_03_seal.cmd || exit /b 1
call run_04_blind_guard.cmd || exit /b 1
call run_10_inventory.cmd "%DATA%" || exit /b 1
call run_20_campaign.cmd "%DATA%" config\extended.json || exit /b 1
call run_30_blind.cmd "" config\extended.json || exit /b 1
echo v0.2.1 strict blind campaign complete. Reveal is manual.
endlocal
