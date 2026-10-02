@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" run_campaign.py --stage standard
exit /b %ERRORLEVEL%
