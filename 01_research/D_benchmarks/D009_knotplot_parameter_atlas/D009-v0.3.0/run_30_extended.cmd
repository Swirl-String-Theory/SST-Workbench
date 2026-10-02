@echo off
setlocal
cd /d "%~dp0"
python run_stage.py --stage extended
exit /b %ERRORLEVEL%
