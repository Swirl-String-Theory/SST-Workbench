@echo off
setlocal
cd /d "%~dp0"
python run_bridge_qualify.py --out exports\p26_bridge
exit /b %ERRORLEVEL%
