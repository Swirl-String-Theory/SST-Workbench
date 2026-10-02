@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo ERROR: .venv not found. Run run_all.cmd setup first.
  exit /b 1
)
.venv\Scripts\python.exe tools_pack_existing_outputs.py
exit /b %ERRORLEVEL%
