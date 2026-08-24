@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python analyze_results.py --stage cert
exit /b %ERRORLEVEL%
