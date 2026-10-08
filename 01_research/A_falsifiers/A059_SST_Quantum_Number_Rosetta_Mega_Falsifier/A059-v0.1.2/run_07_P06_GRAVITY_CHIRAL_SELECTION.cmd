@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_python.cmd -m mega.phase_runner P06
exit /b %ERRORLEVEL%
