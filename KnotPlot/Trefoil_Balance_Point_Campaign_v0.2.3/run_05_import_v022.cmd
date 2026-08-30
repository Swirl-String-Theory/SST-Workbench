@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" import_v022_source.py
exit /b %ERRORLEVEL%
