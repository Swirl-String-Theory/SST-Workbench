@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" verify_panel_200k.py
exit /b %ERRORLEVEL%
