@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_real_blind.cmd ^<input-dir^> [score-config]
  exit /b 2
)
set "A056_INPUT_DIR=%~1"
set "A056_CONFIG=%~2"
if "%A056_CONFIG%"=="" set "A056_CONFIG=configs\e010_real_score.json"
call run_install.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_python.cmd run_instance.py FULL
exit /b %ERRORLEVEL%
