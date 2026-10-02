@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
if "%~2"=="" echo Usage: run_spectral_extension_merge_shards.cmd ^<merged_outdir^> ^<shard1^> [shard2 ...] & exit /b 2
set "OUT=%~1"
shift
set "ARGS="
:collect
if "%~1"=="" goto runmerge
set "ARGS=!ARGS! "%~1""
shift
goto collect
:runmerge
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
".venv\Scripts\python.exe" tools\merge_spectral_extension_shards.py "%OUT%" !ARGS!
exit /b %errorlevel%
