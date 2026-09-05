@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~4"=="" (
  echo Usage: run_archive_single_shard.cmd extra_extended^|full SHARD_INDEX SHARD_COUNT OUTPUT_DIRECTORY
  exit /b 2
)
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
set "CFG=configs\archive_extra_extended.json"
if /I "%~1"=="full" set "CFG=configs\archive_full.json"
".venv\Scripts\python.exe" run_archive_campaign.py --config "%CFG%" --out-dir "%~4" --backend auto --shard-index %~2 --shard-count %~3
exit /b %errorlevel%
