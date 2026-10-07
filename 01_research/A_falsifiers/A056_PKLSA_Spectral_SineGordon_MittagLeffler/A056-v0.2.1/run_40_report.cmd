@echo off
setlocal
cd /d "%~dp0"
.venv\Scripts\python.exe tools\generate_report.py || exit /b 1
