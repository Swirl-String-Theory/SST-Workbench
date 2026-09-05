@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python convert_catalog_kpc.py %*
exit /b %ERRORLEVEL%
