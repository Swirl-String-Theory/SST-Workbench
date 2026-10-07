@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_90_pack_blind.cmd ^<campaign-dir^> & exit /b 2)
python tools\pack_outputs.py --campaign "%~1" --mode blind
exit /b %errorlevel%
