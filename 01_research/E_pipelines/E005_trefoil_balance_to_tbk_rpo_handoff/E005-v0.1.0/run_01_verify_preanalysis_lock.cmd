@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" verify_preanalysis_lock.py
exit /b %ERRORLEVEL%
