@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" run_campaign.py --stage probe
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" verify_resume_continuity.py
exit /b %ERRORLEVEL%
