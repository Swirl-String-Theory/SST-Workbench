@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_03_certify.cmd ^<campaign-dir^> [preset] & exit /b 2)
set "PRESET=%~2"
if "%PRESET%"=="" set "PRESET=basic"
python tools\build_blind_runner.py --campaign "%~1" || exit /b %errorlevel%
python "%~1\blind_runner\run_cert.py" --campaign "%~1" --config "%CD%\configs\cert_%PRESET%.json"
exit /b %errorlevel%
