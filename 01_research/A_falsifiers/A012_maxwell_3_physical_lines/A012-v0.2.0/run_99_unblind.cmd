@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
if "%~1"=="" goto usage
if "%~2"=="" goto usage
set "OUTDIR=%~1"
set "KEY=%~2"
"%PY%" -m sst_maxwell3_blind.cli unblind --blind-report "%OUTDIR%\blind_report.json" --key "%KEY%"
exit /b %errorlevel%
:usage
echo Usage: run_99_unblind.cmd outputs\basic_YYYYMMDD_HHMMSS C:\path\unblind_key.json
echo IMPORTANT: use only after the blind output is frozen.
exit /b 2
