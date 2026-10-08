@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  .venv\Scripts\python.exe tools\check_private_material.py || exit /b 1
) else (
  python tools\check_private_material.py || exit /b 1
)
call "%~dp0run_all.cmd" FREEZE "%~1"
exit /b %ERRORLEVEL%
