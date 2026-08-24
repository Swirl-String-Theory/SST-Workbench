@echo off
rem v0.1.6 cumulative resolver launcher. Intentionally no SETLOCAL: exports INPUT.
set "PFD_ROOT=%~dp0"
set "PFD_RESOLVED=%~dp0build\resolved_input.txt"

if not exist "%~dp0build" mkdir "%~dp0build" >nul 2>nul
if exist "%PFD_RESOLVED%" del /q "%PFD_RESOLVED%" >nul 2>nul

if exist "%~dp0.venv\Scripts\python.exe" goto :venv
where py.exe >nul 2>nul
if not errorlevel 1 goto :pylauncher
where python.exe >nul 2>nul
if not errorlevel 1 goto :python
echo ERROR: Python was not found. Run run_00_install.cmd first.
exit /b 5

:venv
"%~dp0.venv\Scripts\python.exe" "%~dp0resolve_input.py" --explicit "%~1" --repo-dir "%~dp0" --pattern "*_i10000.txt" --out-file "%PFD_RESOLVED%"
goto :after_python

:pylauncher
py -3 "%~dp0resolve_input.py" --explicit "%~1" --repo-dir "%~dp0" --pattern "*_i10000.txt" --out-file "%PFD_RESOLVED%"
goto :after_python

:python
python "%~dp0resolve_input.py" --explicit "%~1" --repo-dir "%~dp0" --pattern "*_i10000.txt" --out-file "%PFD_RESOLVED%"

:after_python
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" exit /b %RC%

if not exist "%PFD_RESOLVED%" (
  echo ERROR: resolver returned success but did not write:
  echo   %PFD_RESOLVED%
  exit /b 4
)

set "INPUT="
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
