@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_campaign.cmd ^<config.json^> ^<outdir^>
  exit /b 2
)
if "%~2"=="" (
  echo Usage: run_campaign.cmd ^<config.json^> ^<outdir^>
  exit /b 2
)
call run_10_prepare.cmd "%~1" "%~2" || exit /b 1
call run_20_blind.cmd "%~1" "%~2" || exit /b 1
call run_30_analyze.cmd "%~1" "%~2" || exit /b 1
call run_35_archive_blind.cmd "%~2" || exit /b 1
echo.
echo BLIND analysis complete: %~2\REPORT_BLIND.md
echo Reveal only after inspecting/saving the blind report:
echo   run_40_reveal.cmd "%~2"
exit /b 0
