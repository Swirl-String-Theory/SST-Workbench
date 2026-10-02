@echo off
setlocal EnableExtensions
cd /d "%~dp0"
".venv\Scripts\python.exe" filesystem_preflight.py
exit /b %ERRORLEVEL%
