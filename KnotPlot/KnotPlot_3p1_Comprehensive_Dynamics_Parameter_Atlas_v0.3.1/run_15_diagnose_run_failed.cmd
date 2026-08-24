@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" diagnose_run_failed.py
exit /b %ERRORLEVEL%
