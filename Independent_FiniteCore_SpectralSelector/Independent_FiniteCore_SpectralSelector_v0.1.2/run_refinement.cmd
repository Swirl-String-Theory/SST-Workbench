@echo off
setlocal
cd /d "%~dp0"
python run_convergence_campaign.py %*
exit /b %ERRORLEVEL%
