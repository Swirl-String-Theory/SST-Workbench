@echo off
setlocal
cd /d "%~dp0"
python analyze.py probe
exit /b %ERRORLEVEL%
