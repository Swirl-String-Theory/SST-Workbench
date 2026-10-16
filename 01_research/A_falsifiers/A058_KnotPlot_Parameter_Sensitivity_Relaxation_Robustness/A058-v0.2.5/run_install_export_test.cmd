@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_python.cmd tools\install_test_export.py
exit /b %ERRORLEVEL%
