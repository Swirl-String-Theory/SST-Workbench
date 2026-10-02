@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_catalog_one.cmd knot_3.1& exit /b 2)
python run_catalog_batch.py --one "%~1"
exit /b %ERRORLEVEL%
