@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_real_blind.cmd INPUT_DIR [BASIC^|FULL^|CERTIFY]
  exit /b 2
)
set "A056_INPUT_DIR=%~f1"
set "MODE=%~2"
if "%MODE%"=="" set "MODE=FULL"
call run_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
.venv\Scripts\python.exe run_instance.py %MODE%
exit /b %ERRORLEVEL%
