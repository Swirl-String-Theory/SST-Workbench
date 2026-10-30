@echo off
setlocal
cd /d "%~dp0"
py -3.14 -B run_all.py %*
exit /b %ERRORLEVEL%
