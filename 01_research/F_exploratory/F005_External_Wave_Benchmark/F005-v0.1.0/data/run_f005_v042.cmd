@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."
call "run_all_v042.cmd"
exit /b %errorlevel%
