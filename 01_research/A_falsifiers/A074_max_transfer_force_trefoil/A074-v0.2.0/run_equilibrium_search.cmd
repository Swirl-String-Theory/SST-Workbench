@echo off
setlocal
cd /d "%~dp0"
python -m experiment.search_stationary %*
exit /b %errorlevel%
