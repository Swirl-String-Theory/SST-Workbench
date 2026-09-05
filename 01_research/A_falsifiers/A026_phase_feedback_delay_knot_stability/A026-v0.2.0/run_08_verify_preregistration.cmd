@echo off
setlocal
cd /d "%~dp0"
.venv\Scripts\python.exe verify_preregistration.py
exit /b %ERRORLEVEL%
