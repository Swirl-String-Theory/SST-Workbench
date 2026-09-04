@echo off
setlocal
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
.venv\Scripts\python.exe scripts\selftest.py
