@echo off
setlocal
cd /d "%~dp0"
python run_refinement.py %*
exit /b %ERRORLEVEL%
