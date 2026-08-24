@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" run_stage.py --stage extended
exit /b %ERRORLEVEL%
