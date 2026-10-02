@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" bridge.py summarize --mode selected
exit /b %ERRORLEVEL%
