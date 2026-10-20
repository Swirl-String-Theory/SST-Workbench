@echo off
setlocal
call "%~dp0run_g5_diagnostic.cmd" --replay-v025
exit /b %errorlevel%
