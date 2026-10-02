@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" generate_seeds.py
exit /b %ERRORLEVEL%
