@echo off
setlocal
cd /d "%~dp0"
set OUT=%~1
if "%OUT%"=="" (
  echo Usage: run_40_reveal.cmd outputs\basic_YYYYMMDD_HHMMSS
  exit /b 2
)
.venv\Scripts\python.exe -m sst_chiral.reveal "%OUT%" || exit /b 1
exit /b 0
