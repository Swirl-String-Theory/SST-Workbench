@echo off
setlocal
cd /d "%~dp0"
python run_pipeline.py --python-only %*
exit /b %errorlevel%
