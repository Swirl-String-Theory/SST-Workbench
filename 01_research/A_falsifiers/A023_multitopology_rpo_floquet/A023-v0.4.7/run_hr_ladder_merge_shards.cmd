@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~3"=="" echo Usage: run_hr_ladder_merge_shards.cmd ^<merged_output_dir^> ^<shard_output_1^> ^<shard_output_2^> [...] & exit /b 2
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
".venv\Scripts\python.exe" tools\merge_hr_ladder_shards.py %*
exit /b %errorlevel%
