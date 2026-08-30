@echo off
setlocal
cd /d "%~dp0"
if "%QHP_PROGRESS_EVERY%"=="" set QHP_PROGRESS_EVERY=15
".venv\Scripts\python.exe" run_campaign.py --stage cold_overlap --progress-every=%QHP_PROGRESS_EVERY%
exit /b %ERRORLEVEL%
