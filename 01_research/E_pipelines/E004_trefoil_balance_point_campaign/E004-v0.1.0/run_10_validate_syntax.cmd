@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" validate_kpc.py
exit /b %ERRORLEVEL%
