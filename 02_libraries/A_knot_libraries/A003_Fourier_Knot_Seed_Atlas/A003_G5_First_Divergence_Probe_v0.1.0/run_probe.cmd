@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>&1 || (echo ERROR: Python unavailable. Activate SST-Workbench .venv & exit /b 3)
python probe.py %*
exit /b %ERRORLEVEL%
