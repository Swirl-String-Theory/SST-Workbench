@echo off
setlocal
cd /d "%~dp0"
.venv\Scripts\python.exe tools\package_outputs.py || exit /b 1
