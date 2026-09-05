@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" (
  echo ERROR: run_focus_link_9p2p20.cmd is a historical KnotPlot/reference focus runner.
  echo v0.3.0 primary discovery is the self-contained PTSA atlas.
  echo Supply an explicit external KnotPlot dataset path, for example:
  echo   run_focus_link_9p2p20.cmd "C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
  popd
  exit /b 2
)
echo REFERENCE CONTROL ONLY: external KnotPlot dataset = %DATA%
call run_20_campaign.cmd "%DATA%" config\focus_link_9p2p20.json || exit /b 1
call run_30_blind.cmd "" config\focus_link_9p2p20.json

popd
endlocal
