@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe seal_blind_results.py
exit /b %errorlevel%
