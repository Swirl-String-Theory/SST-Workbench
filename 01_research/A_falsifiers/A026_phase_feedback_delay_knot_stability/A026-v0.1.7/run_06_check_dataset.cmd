@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: run run_00_install.cmd first.
  exit /b 5
)
if "%~1"=="" (
  ".venv\Scripts\python.exe" check_dataset.py "build\resolved_input.txt"
) else (
  ".venv\Scripts\python.exe" check_dataset.py "%~1"
)
exit /b %ERRORLEVEL%
