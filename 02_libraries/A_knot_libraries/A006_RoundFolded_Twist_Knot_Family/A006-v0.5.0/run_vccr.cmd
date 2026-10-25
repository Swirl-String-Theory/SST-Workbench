@echo off
setlocal
cd /d "%~dp0" || exit /b 1
py -3 -m vccr.dispatch %*
exit /b %errorlevel%
