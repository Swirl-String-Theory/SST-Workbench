@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if exist "%PY%" goto havepy
set "PY=..\.venv\Scripts\python.exe"
if exist "%PY%" goto havepy
set "PY=py -3"
:havepy

%PY% restore_a054_native.py
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo A054 native runner restore FAILED with exit code %RC%.
  exit /b %RC%
)

echo.
echo A054 native runner restore PASS.
echo You can now rerun A055 run_all.cmd.
exit /b 0
