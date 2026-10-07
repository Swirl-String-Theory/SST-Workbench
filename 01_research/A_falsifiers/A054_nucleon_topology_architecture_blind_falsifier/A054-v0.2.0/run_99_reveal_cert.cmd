@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_99_reveal_cert.cmd ^<campaign-dir^> & exit /b 2)
python -m a054_ntaf.cli reveal-cert --campaign "%~1" || exit /b %errorlevel%
python tools\pack_outputs.py --campaign "%~1" --mode revealed
exit /b %errorlevel%
