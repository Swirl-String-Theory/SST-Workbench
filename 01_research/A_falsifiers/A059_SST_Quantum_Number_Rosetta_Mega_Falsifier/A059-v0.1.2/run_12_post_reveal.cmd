@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_python.cmd -m mega.reveal_analysis
exit /b %ERRORLEVEL%
