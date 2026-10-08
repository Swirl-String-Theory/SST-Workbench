@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "KP=%~1"
set "WB=%~2"
set "STARTIN=%~3"
if "%WB%"=="" (
  if not "%SST_WORKBENCH%"=="" set "WB=%SST_WORKBENCH%"
)
if "%WB%"=="" (
  if not "%SST_WORKBENCH_ROOT%"=="" set "WB=%SST_WORKBENCH_ROOT%"
)
call run_install.cmd || exit /b 1
call run_10_prepare_campaign.cmd pilot || exit /b 1
call run_all.cmd SELFTEST "%WB%" || exit /b 1
call run_all.cmd FREEZE "%WB%" || exit /b 1
call run_20_run_knotplot.cmd pilot "%KP%" "%STARTIN%" || exit /b 1
call run_all.cmd FULL "%WB%"
exit /b %ERRORLEVEL%
