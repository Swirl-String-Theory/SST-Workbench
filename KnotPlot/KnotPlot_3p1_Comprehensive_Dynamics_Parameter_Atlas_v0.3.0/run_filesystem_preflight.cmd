@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python filesystem_preflight.py
exit /b %ERRORLEVEL%
