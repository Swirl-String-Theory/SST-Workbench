@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" analyze_matrix.py
exit /b %ERRORLEVEL%
