@echo off
setlocal
cd /d "%~dp0"
python run_stage.py --stage probe
exit /b %ERRORLEVEL%
