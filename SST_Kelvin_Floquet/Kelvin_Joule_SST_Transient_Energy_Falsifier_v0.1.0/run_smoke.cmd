@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe call run_install.cmd
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe run_all_checks.py --backend auto
exit /b %errorlevel%
