@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call scripts\resolve_python.cmd
"%PYTHON%" scripts\run_spectral_cmd.py %*
exit /b %errorlevel%
