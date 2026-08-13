@echo off
setlocal
cd /d "%~dp0"
call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe prepare_blind_campaign.py
exit /b %errorlevel%
