@echo off
setlocal EnableExtensions
call "%~dp0_paths.cmd"
cd /d "%ROOT%"
if "%~1"=="" (echo Usage: run_03_blind_campaign.cmd C:\path\to\campaign& exit /b 1)
"%PY%" run_blind.py --campaign "%~1" --config configs\preregister_v0.2.0.json
exit /b %ERRORLEVEL%
