@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" dispatch_target.py --prefer v048 confirm-v048 --mode selected
exit /b %ERRORLEVEL%
