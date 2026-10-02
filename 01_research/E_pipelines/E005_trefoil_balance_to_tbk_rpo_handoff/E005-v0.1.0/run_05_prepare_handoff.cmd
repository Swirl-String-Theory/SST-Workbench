@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" bridge.py prepare
exit /b %ERRORLEVEL%
