@echo off
setlocal
cd /d "%~dp0"
set "REPO=%CD%"
if not exist "%REPO%\.sst-workbench-root" (
  if exist "%CD%\..\.sst-workbench-root" (
    for %%I in ("%CD%\..") do set "REPO=%%~fI"
  )
)
if not exist "%REPO%\.sst-workbench-root" (
  echo ERROR: Could not locate SST-Workbench root.
  echo Extract this patch directly inside C:\workspace\projects\SST-Workbench\
  exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python launcher "py" not found.
  exit /b 2
)
py -m pip install -r "%CD%\requirements-patch.txt"
if errorlevel 1 exit /b %errorlevel%

py "%CD%\scripts\validate_registry_v2.py" --repo "%REPO%"
exit /b %errorlevel%
