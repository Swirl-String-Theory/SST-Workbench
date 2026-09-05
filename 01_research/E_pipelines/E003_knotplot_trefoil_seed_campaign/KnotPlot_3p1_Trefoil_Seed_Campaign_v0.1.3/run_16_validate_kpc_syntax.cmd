@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" validate_kpc_syntax.py
exit /b %ERRORLEVEL%
