@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_python.cmd -m mega.phase_runner P07
exit /b %ERRORLEVEL%
