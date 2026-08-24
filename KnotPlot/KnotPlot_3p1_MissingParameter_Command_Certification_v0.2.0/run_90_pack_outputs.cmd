@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python pack_outputs.py
exit /b %ERRORLEVEL%
