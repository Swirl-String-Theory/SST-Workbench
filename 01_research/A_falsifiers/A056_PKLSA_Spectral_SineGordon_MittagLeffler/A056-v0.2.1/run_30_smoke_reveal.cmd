@echo off
setlocal
cd /d "%~dp0"
.venv\Scripts\python.exe tools\reveal_smoke.py || exit /b 1
