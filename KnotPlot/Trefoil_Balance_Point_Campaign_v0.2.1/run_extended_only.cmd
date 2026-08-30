@echo off
setlocal EnableExtensions
cd /d "%~dp0"
".venv\Scripts\python.exe" generate_extended_metric_neutral.py
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" validate_kpc.py
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" run_campaign.py --stage extended
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" verify_resume_continuity.py
exit /b %ERRORLEVEL%
