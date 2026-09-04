@echo off
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
call run_20_campaign.cmd "%DATA%" config\focus_trefoil_3p1.json || exit /b 1
call run_30_blind.cmd "" config\focus_trefoil_3p1.json
