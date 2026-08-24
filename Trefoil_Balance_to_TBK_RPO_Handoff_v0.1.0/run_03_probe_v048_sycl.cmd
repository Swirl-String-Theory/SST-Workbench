@echo off
setlocal EnableExtensions
cd /d "%~dp0"
".venv\Scripts\python.exe" probe_v048_sycl.py
exit /b %ERRORLEVEL%
