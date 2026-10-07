@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_90_pack_blind.cmd ^<campaign-dir^> & exit /b 2)
set "PY=%CD%\.venv\Scripts\python.exe"
"%PY%" tools\pack_outputs.py --campaign "%~1" --mode blind
exit /b %errorlevel%
