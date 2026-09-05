@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage:
  echo   run_sweep.cmd --qhp-min=q,h,p --qhp-max=q,h,p [options]
  echo.
  ".venv\Scripts\python.exe" sweep.py --help
  exit /b 2
)
".venv\Scripts\python.exe" sweep.py %*
exit /b %ERRORLEVEL%
