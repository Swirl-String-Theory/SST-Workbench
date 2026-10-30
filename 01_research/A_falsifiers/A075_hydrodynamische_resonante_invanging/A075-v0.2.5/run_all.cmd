@echo off
setlocal
cd /d "%~dp0"
python run_instance.py %*
exit /b %errorlevel%
