@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd
if errorlevel 1 exit /b %errorlevel%
"%CD%\.venv\Scripts\python.exe" -m maxwell_sst.cli demo --out 4_outputs_demo
exit /b %ERRORLEVEL%
