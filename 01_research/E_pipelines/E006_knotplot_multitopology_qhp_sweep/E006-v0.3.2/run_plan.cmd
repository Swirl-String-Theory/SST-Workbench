@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" sweep.py %* --dry-run
exit /b %ERRORLEVEL%
