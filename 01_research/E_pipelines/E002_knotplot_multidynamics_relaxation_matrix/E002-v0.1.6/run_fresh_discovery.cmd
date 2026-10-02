@echo off
setlocal EnableExtensions
cd /d "%~dp0"

python archive_previous_run.py
if errorlevel 1 exit /b %ERRORLEVEL%

python kpc_audit.py
if errorlevel 1 exit /b %ERRORLEVEL%

call run_all.cmd
if errorlevel 1 (
  echo.
  echo DISCOVERY FAILED. Inspect:
  echo   preflight\
  echo   logs\
  exit /b %ERRORLEVEL%
)

call run_analyze.cmd
exit /b %ERRORLEVEL%
