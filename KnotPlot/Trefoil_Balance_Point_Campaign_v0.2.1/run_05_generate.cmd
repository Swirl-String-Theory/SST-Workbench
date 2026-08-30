@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" generate_kpc_safe.py
exit /b %ERRORLEVEL%
