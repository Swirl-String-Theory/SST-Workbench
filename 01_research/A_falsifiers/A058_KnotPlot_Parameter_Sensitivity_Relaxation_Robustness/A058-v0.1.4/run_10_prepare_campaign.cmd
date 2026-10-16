@echo off
setlocal
cd /d "%~dp0"
set "TIER=%~1"
if "%TIER%"=="" set "TIER=pilot"
call run_python.cmd tools\generate_campaign.py --tier %TIER%
exit /b %ERRORLEVEL%
