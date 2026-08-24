@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python run_catalog_batch.py %*
exit /b %ERRORLEVEL%
