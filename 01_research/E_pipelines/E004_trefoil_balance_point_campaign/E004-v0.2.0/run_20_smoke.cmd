@echo off
setlocal
cd /d "%~dp0"
echo Full 10k smoke of first and last frozen K31 zero-bracket settings.
".venv\Scripts\python.exe" run_campaign.py --smoke
exit /b %ERRORLEVEL%
