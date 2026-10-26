@echo off
setlocal
cd /d "%~dp0"
python -m experiment.run_euler %*
exit /b %errorlevel%
