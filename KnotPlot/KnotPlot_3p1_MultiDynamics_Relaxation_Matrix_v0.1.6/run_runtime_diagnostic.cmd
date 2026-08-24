@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python diagnose_knotplot_runtime.py
exit /b %ERRORLEVEL%
