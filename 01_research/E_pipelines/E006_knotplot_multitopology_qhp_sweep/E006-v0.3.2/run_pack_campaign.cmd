@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
 echo Usage: run_pack_campaign.cmd campaign_name
 exit /b 2
)
".venv\Scripts\python.exe" pack_campaign.py "%~1"
exit /b %ERRORLEVEL%
