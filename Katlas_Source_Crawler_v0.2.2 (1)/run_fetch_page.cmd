@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_fetch_page.cmd K12a1
  exit /b 2
)
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
.venv\Scripts\python.exe -m katlas_source.cli --config config.json fetch-page "%~1"
