@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (python run_all.py PILOT) else (python run_all.py %1)
exit /b %errorlevel%
