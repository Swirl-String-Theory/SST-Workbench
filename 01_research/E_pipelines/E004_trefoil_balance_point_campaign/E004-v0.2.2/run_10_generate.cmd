@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" generate_kpc.py
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" validate_kpc.py
exit /b %ERRORLEVEL%
