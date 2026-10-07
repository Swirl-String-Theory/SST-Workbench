@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_99_reveal_cert.cmd ^<campaign-dir^> & exit /b 2)
set "PY=%CD%\.venv\Scripts\python.exe"
"%PY%" -m a054_ntaf.cli reveal-cert --campaign "%~1" || exit /b %errorlevel%
"%PY%" tools\pack_outputs.py --campaign "%~1" --mode revealed
exit /b %errorlevel%
