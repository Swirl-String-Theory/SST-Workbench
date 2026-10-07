@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_03_certify.cmd ^<campaign-dir^> [preset] & exit /b 2)
set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (echo [ERROR] Missing .venv. Run run_00_install.cmd first. & exit /b 2)
set "PRESET=%~2"
if "%PRESET%"=="" set "PRESET=basic"
"%PY%" tools\build_blind_runner.py --campaign "%~1" || exit /b %errorlevel%
"%PY%" "%~1\blind_runner\run_cert.py" --campaign "%~1" --config "%CD%\configs\cert_%PRESET%.json"
exit /b %errorlevel%
