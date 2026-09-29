@echo off
set "PACKAGE_ROOT=%~dp0"
cd /d "%PACKAGE_ROOT%"
if not defined SST_WORKBENCH_ROOT if exist "C:\workspace\projects\SST-Workbench" set "SST_WORKBENCH_ROOT=C:\workspace\projects\SST-Workbench"
if defined SST_SHARED_VENV (
  set "VENV=%SST_SHARED_VENV%"
) else (
  set "VENV=%PACKAGE_ROOT%.venv"
)
set "PY=%VENV%\Scripts\python.exe"
if not exist "%PY%" (
  echo [3_MAXWELL] Python venv not found: "%PY%"
  echo [3_MAXWELL] Run run_00_install.cmd first.
  exit /b 2
)
if not defined SST_NATIVE_THREADS set "SST_NATIVE_THREADS=16"
exit /b 0
