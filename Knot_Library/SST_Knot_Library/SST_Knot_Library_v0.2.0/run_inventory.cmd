@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo ERROR: run run_all.cmd first.
  exit /b 3
)
.venv\Scripts\python.exe -m sst_knotlib inventory-sources --require-no-move
exit /b %errorlevel%
