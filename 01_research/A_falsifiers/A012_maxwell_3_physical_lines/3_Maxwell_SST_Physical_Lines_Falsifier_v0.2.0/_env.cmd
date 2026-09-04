@echo off
set "WORKBENCH=%~dp0"
cd /d "%WORKBENCH%"
set "VENV=%WORKBENCH%..\..\.venv"
set "PY=%VENV%\Scripts\python.exe"
if not exist "%PY%" (
  echo [3_MAXWELL] Shared venv not found: "%PY%"
  echo [3_MAXWELL] Run run_00_install.cmd first.
  exit /b 2
)
if not defined KNOTS_DIR set "KNOTS_DIR=%WORKBENCH%..\..\KnotPlot\knots\final"
if not defined SST_NATIVE_THREADS set "SST_NATIVE_THREADS=16"
exit /b 0
