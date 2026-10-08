@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PY=py -3"
if exist "%~dp0..\A054-v0.2.0-r2\.venv\Scripts\python.exe" set "PY=%~dp0..\A054-v0.2.0-r2\.venv\Scripts\python.exe"

%PY% restore_and_verify.py %*
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" (
  echo A054 native restore FAILED with exit code %RC%.
  exit /b %RC%
)
echo A054 native restore VERIFIED.
echo Now rerun A055 run_all.cmd.
exit /b 0
