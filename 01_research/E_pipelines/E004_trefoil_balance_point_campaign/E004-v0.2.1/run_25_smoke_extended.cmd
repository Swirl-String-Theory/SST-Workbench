@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" run_campaign.py --stage extended --smoke
exit /b %ERRORLEVEL%
