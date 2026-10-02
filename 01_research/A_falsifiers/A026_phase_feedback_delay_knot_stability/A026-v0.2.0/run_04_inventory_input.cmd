@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" inventory_input.py
  set "RC=%ERRORLEVEL%"
  exit /b %RC%
)

where py.exe >nul 2>nul
if not errorlevel 1 (
  py -3 inventory_input.py
  set "RC=%ERRORLEVEL%"
  exit /b %RC%
)

where python.exe >nul 2>nul
if not errorlevel 1 (
  python inventory_input.py
  set "RC=%ERRORLEVEL%"
  exit /b %RC%
)

echo ERROR: Python was not found.
exit /b 5
