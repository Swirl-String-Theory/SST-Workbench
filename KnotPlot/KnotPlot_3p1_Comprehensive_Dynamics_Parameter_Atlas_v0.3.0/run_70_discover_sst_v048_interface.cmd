@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python discover_sst_v048_interface.py
exit /b %ERRORLEVEL%
