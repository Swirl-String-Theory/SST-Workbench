@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
".venv\Scripts\python.exe" analyze.py
exit /b %ERRORLEVEL%
