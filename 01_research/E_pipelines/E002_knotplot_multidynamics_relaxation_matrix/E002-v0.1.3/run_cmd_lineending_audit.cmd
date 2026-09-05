@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python audit_cmd_line_endings.py
exit /b %ERRORLEVEL%
