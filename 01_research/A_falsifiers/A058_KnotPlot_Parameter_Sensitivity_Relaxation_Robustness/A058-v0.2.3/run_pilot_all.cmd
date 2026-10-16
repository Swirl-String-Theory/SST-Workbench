@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_install.cmd
if errorlevel 1 exit /b 1
call run_10_prepare_campaign.cmd
if errorlevel 1 exit /b 1
call run_all.cmd SELFTEST "%SST_WORKBENCH%"
if errorlevel 1 exit /b 1
call run_freeze.cmd "%SST_WORKBENCH%"
if errorlevel 1 exit /b 1
call run_20_run_knotplot.cmd
if errorlevel 1 exit /b 1
call run_all.cmd FULL "%SST_WORKBENCH%"
exit /b %ERRORLEVEL%
