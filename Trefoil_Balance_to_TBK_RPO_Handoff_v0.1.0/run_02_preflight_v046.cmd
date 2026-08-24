@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" bridge.py preflight --prefer v046
exit /b %ERRORLEVEL%
