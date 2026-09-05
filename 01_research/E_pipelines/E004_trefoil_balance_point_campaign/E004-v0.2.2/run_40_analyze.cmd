@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" analyze.py
exit /b %ERRORLEVEL%
