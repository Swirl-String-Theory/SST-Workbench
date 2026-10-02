@echo off
setlocal
cd /d "%~dp0"
echo WARNING: debug/smoke runner. It executes the first FULL 10000-iteration seed only.
".venv\Scripts\python.exe" run_campaign.py --stage full --limit 1
exit /b %ERRORLEVEL%
