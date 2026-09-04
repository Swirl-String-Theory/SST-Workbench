@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" run_resolver_selftest.py
) else (
  py -3 run_resolver_selftest.py
)
exit /b %ERRORLEVEL%
