@echo off
setlocal
cd /d "%~dp0"
python -m experiment.run_euler_pilot
exit /b %errorlevel%
