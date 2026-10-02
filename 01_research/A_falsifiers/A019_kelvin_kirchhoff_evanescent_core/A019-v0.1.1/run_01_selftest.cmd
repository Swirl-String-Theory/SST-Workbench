@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call config\paths.cmd
if not defined KK_PY set "KK_PY=%CD%\.venv\Scripts\python.exe"
set "THREADS=%~1"
if "%THREADS%"=="" set "THREADS=4"
"%KK_PY%" run_selftest.py --require-native --threads %THREADS%
exit /b %errorlevel%
