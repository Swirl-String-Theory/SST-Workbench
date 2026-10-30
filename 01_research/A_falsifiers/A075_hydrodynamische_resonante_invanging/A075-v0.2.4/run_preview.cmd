@echo off
setlocal
cd /d "%~dp0"
python run_preview.py --profile PREVIEW %*
exit /b %errorlevel%
