@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "PYTHON=.venv\Scripts\python.exe"
) else (
  set "PYTHON=python"
)
echo [SST] Native preflight using "%PYTHON%"
"%PYTHON%" run_native_preflight.py
if errorlevel 1 (
  echo [SST] Native preflight failed. Campaign not started.
  exit /b %errorlevel%
)
"%PYTHON%" scripts\run_all_cmd.py %*
exit /b %errorlevel%
