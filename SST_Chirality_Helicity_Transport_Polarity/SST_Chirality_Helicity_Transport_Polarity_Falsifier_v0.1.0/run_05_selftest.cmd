@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  call run_00_setup.cmd
  if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -m sst_chiral.selftest
if errorlevel 1 exit /b 1
exit /b 0
