@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_report.cmd outputs\run_all_YYYYMMDD_HHMMSS\extended
  exit /b 2
)
if not exist ".venv\Scripts\python.exe" (echo Missing .venv.& exit /b 2)
".venv\Scripts\python.exe" run_report.py "%~1"
exit /b %errorlevel%
