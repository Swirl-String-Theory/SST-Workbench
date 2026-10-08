@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if exist "%PY%" goto havepy
set "PY=..\.venv\Scripts\python.exe"
if exist "%PY%" goto havepy
set "PY=py -3"
:havepy
%PY% restore_a054_native.py --verify-only
exit /b %ERRORLEVEL%
