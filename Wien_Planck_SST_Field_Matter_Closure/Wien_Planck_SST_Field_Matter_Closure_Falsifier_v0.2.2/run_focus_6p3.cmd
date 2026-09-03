@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
call run_20_campaign.cmd "%DATA%" config\focus_6p3.json || exit /b 1
call run_30_blind.cmd "" config\focus_6p3.json

popd
endlocal
