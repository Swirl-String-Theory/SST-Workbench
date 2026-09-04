@echo off
rem NOTE: intentionally no SETLOCAL. Exports INPUT to caller.
set "PFD_RESOLVED=%~dp0build\resolved_input.txt"
if not exist "%~dp0build" mkdir "%~dp0build" >nul 2>nul
if exist "%PFD_RESOLVED%" del /q "%PFD_RESOLVED%" >nul 2>nul

set "PFD_PY="
if exist "%~dp0.venv\Scripts\python.exe" set "PFD_PY=%~dp0.venv\Scripts\python.exe"
if not defined PFD_PY (
  where py.exe >nul 2>nul
  if not errorlevel 1 set "PFD_PY=py -3"
)
if not defined PFD_PY (
  where python.exe >nul 2>nul
  if not errorlevel 1 set "PFD_PY=python"
)
if not defined PFD_PY (
  echo ERROR: Python was not found. Run run_00_install.cmd first.
  exit /b 5
)

%PFD_PY% "%~dp0resolve_input.py" --explicit "%~1" --repo-dir "%~dp0" --pattern "*_i10000.txt" --out-file "%PFD_RESOLVED%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" exit /b %RC%
if not exist "%PFD_RESOLVED%" (
  echo ERROR: resolver returned success but did not write %PFD_RESOLVED%
  exit /b 4
)
set /p INPUT=<"%PFD_RESOLVED%"
if not defined INPUT (
  echo ERROR: resolved input path is empty.
  exit /b 4
)
if not exist "%INPUT%" (
  echo ERROR: resolved input directory does not exist:
  echo   %INPUT%
  exit /b 4
)
echo [PFD] Resolved input: %INPUT%
exit /b 0
