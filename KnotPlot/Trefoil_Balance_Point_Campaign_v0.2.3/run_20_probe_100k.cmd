@echo off
setlocal
cd /d "%~dp0"
if not exist "analysis\resume_checks" mkdir "analysis\resume_checks"
".venv\Scripts\python.exe" run_campaign.py --stage probe
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" verify_resume_continuity.py
exit /b %ERRORLEVEL%
