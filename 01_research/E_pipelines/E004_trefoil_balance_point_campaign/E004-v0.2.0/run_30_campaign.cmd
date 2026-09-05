@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" run_campaign.py
exit /b %ERRORLEVEL%
