@echo off
setlocal EnableExtensions
cd /d "%~dp0"
".venv\Scripts\python.exe" verify_existing_screen.py
exit /b %ERRORLEVEL%
