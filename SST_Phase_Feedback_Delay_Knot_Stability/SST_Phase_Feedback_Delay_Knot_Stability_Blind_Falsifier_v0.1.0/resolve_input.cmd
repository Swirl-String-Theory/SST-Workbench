@echo off
rem NOTE: intentionally no SETLOCAL. Exports INPUT to caller.

if /I "%~1"=="/h" goto :usage
if /I "%~1"=="-h" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="/?" goto :usage

set "EXPLICIT=%~1"
set "REPO_DIR=%~2"
set "PATTERN=%~3"
set "OUT_FILE=%~4"

if "%REPO_DIR%"=="" for %%I in ("%~dp0.") do set "REPO_DIR=%%~fI"
if "%PATTERN%"=="" set "PATTERN=*_i10000.txt"
if "%OUT_FILE%"=="" set "OUT_FILE=%~dp0build\resolved_input.txt"

if not exist "%~dp0build" mkdir "%~dp0build" >nul 2>nul
if exist "%OUT_FILE%" del /q "%OUT_FILE%" >nul 2>nul

python "%~dp0resolve_input.py" --explicit "%EXPLICIT%" --repo-dir "%REPO_DIR%" --pattern "%PATTERN%" --out-file "%OUT_FILE%"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" exit /b %RC%
if not exist "%OUT_FILE%" (
  echo ERROR: resolver returned success but did not write "%OUT_FILE%"
  exit /b 4
)
set /p INPUT=<"%OUT_FILE%"
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

:usage
echo Usage:
echo   resolve_input.cmd [explicit_dir] [repo_dir] [pattern] [out_file]
echo.
echo Defaults:
echo   repo_dir  = script directory
echo   pattern   = *_i10000.txt
echo   out_file  = build\resolved_input.txt
echo.
echo Example:
echo   resolve_input.cmd "C:\path\to\matrix" "%~dp0" "*_i10000.txt" "%~dp0build\resolved_input.txt"
exit /b 0