@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" dispatch_target.py --prefer v046 full-v046 --mode selected
exit /b %ERRORLEVEL%
