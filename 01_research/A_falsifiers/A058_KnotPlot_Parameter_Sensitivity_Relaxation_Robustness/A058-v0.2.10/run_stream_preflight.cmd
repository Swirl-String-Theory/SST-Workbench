@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist "private\install_test_runtime\defaults.json" (
  echo STREAM PREFLIGHT: install calibration missing. Run run_install.cmd first.
  exit /b 2
)
if not exist "campaign\manifest_pilot.json" (
  call run_10_prepare_campaign.cmd
  if errorlevel 1 exit /b 1
)
call run_python.cmd tools\run_knotplot_campaign.py --tier pilot --preflight-only --exe "%~1" --workdir "%~2"
exit /b %ERRORLEVEL%
