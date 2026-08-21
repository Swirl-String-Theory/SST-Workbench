@echo off
rem NOTE: intentionally no SETLOCAL. Exports INPUT to caller.
set "PFD_RESOLVED=%~dp0build\resolved_input.txt"
if not exist "%~dp0build" mkdir "%~dp0build" >nul 2>nul
if exist "%PFD_RESOLVED%" del /q "%PFD_RESOLVED%" >nul 2>nul

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0resolve_input.ps1" -Explicit "%~1" -RepoDir "%~dp0" -Pattern "*_i10000.txt" -OutFile "%PFD_RESOLVED%"
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
