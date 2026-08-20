@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
".venv\Scripts\python.exe" tests\smoke_test.py
exit /b %errorlevel%
