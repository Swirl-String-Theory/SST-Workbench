@echo off
setlocal EnableExtensions
cd /d "%~dp0"
py -3 restore_and_verify.py --verify-only %*
exit /b %ERRORLEVEL%
