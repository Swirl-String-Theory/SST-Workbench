@echo off
setlocal
cd /d "%~dp0"
call run_python.cmd tools\generate_campaign.py --tier pilot
exit /b %ERRORLEVEL%
