@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
if "%~1"=="" goto usage
if "%~2"=="" goto usage
"%PY%" -m sst_maxwell3_blind.cli unblind --blind-report "%~1\blind_report.json" --key "%~2"
exit /b %errorlevel%
:usage
echo Usage: run_99_unblind.cmd outputs\PROFILE_YYYYMMDD_HHMMSS C:\path\unblind_key.json
echo IMPORTANT: only after FROZEN_SHA256.json exists.
exit /b 2
