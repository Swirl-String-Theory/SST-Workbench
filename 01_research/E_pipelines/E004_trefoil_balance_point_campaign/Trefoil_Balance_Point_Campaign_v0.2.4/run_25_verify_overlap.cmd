@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" verify_overlap_200k.py
exit /b %ERRORLEVEL%
