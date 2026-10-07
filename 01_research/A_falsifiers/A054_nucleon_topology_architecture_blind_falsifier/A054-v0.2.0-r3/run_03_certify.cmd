@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_03_certify.cmd ^<campaign-dir^> [preset] [resume^|fresh] & exit /b 2)
set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (echo [ERROR] Missing .venv. Run run_00_install.cmd first. & exit /b 2)
set "PRESET=%~2"
if "%PRESET%"=="" set "PRESET=basic"
set "MODE=%~3"
set "MODEARG="
if /I "%MODE%"=="resume" set "MODEARG=--resume"
if /I "%MODE%"=="fresh" set "MODEARG=--fresh"
if not "%MODE%"=="" if "%MODEARG%"=="" (echo [ERROR] Third argument must be resume or fresh. & exit /b 2)
set "REQ="
if /I "%PRESET%"=="extended" set "REQ=--require-openmp"
if /I "%PRESET%"=="full" set "REQ=--require-openmp"
"%PY%" tools\build_blind_runner.py --campaign "%~1" %REQ% || exit /b %errorlevel%
"%PY%" "%~1\blind_runner\run_cert.py" --campaign "%~1" --config "%CD%\configs\cert_%PRESET%.json" %MODEARG%
exit /b %errorlevel%
