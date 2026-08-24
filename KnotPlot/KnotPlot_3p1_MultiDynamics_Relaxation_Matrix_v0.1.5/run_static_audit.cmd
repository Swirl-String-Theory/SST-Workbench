@echo off
setlocal
cd /d "%~dp0"
python kpc_audit.py
exit /b %ERRORLEVEL%
