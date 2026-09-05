@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv 2>nul || python -m venv .venv || exit /b 1
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b %ERRORLEVEL%
".venv\Scripts\python.exe" -m pip install -r requirements.txt
exit /b %ERRORLEVEL%
