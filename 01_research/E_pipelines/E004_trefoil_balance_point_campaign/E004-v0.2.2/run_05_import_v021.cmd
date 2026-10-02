@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" import_v021_source.py
exit /b %ERRORLEVEL%
