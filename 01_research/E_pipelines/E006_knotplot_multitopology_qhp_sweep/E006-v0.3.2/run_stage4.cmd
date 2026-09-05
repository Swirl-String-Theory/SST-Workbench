@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  call run_00_install.cmd
  if errorlevel 1 exit /b %ERRORLEVEL%
)
".venv\Scripts\python.exe" stage_runner.py stage4_rest %*
exit /b %ERRORLEVEL%
