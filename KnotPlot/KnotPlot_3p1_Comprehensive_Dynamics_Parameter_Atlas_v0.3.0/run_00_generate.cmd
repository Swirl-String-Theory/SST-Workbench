@echo off
setlocal
cd /d "%~dp0"
python generate_kpc.py
exit /b %ERRORLEVEL%
