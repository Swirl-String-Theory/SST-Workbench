@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~2"=="" (
  echo Usage: run_archive_resume.cmd extra_extended^|full OUTPUT_DIRECTORY [extra python args]
  exit /b 2
)
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "MODE=%~1"
set "OUT=%~2"
set "CFG=configs\archive_extra_extended.json"
if /I "%MODE%"=="full" set "CFG=configs\archive_full.json"
".venv\Scripts\python.exe" run_archive_campaign.py --config "%CFG%" --out-dir "%OUT%" --backend auto
exit /b %errorlevel%
