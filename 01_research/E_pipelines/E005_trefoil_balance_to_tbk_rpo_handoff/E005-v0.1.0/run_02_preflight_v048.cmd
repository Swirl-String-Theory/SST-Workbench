@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" bridge.py preflight --prefer v048
exit /b %ERRORLEVEL%
