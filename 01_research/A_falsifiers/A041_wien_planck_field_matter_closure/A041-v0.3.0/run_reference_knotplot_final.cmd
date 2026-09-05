@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
echo REFERENCE CONTROL ONLY: external KnotPlot final dataset
call run_10_inventory.cmd "%DATA%" || exit /b 1
call run_15_seed_qualify.cmd "%DATA%" config\basic.json || exit /b 1
call run_20_campaign.cmd "%DATA%" config\basic.json || exit /b 1
call run_30_blind.cmd "" config\basic.json || exit /b 1
popd
endlocal
