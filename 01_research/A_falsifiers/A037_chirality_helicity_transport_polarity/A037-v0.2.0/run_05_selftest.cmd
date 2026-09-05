@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe call run_00_setup.cmd || exit /b 1
.venv\Scripts\python.exe -m sst_chiral.selftest || exit /b 1
exit /b 0
