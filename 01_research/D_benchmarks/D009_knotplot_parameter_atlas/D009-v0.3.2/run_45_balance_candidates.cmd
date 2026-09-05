@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" balance_candidates.py
exit /b %ERRORLEVEL%
