@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
if "%~1"=="" (echo Usage: run_90_verify_frozen.cmd outputs\basic_YYYYMMDD_HHMMSS& exit /b 2)
"%PY%" -m sst_maxwell3_blind.cli verify-frozen --outdir "%~1"
exit /b %errorlevel%
