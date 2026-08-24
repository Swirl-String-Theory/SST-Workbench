@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" bridge.py verify-lock --mode selected
exit /b %ERRORLEVEL%
