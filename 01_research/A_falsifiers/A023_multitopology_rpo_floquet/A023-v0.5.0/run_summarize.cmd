@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_summarize.cmd ^<output_directory^>
  exit /b 2
)
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
".venv\Scripts\python.exe" tools\summarize_result.py "%~1"
exit /b %errorlevel%
