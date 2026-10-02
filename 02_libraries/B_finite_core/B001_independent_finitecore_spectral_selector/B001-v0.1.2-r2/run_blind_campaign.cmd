@echo off
setlocal
cd /d "%~dp0"
python run_blind_campaign.py %*
exit /b %ERRORLEVEL%
