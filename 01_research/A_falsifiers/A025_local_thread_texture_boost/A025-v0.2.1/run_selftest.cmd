@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd
if errorlevel 1 exit /b %errorlevel%
.venv\Scripts\python.exe run_selftest.py --require-native
exit /b %errorlevel%
