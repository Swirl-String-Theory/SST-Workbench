@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_lookup.cmd 3_1
  exit /b 2
)
if not exist .venv\Scripts\python.exe py -3 -m venv .venv
.venv\Scripts\python.exe -m katlas_source.cli --config config.json lookup "%~1"
