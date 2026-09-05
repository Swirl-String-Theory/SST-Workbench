@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: run_one.cmd ^<path-to-*_final.txt^> [resolution]
  exit /b 2
)
if not exist ".venv\Scripts\python.exe" call run_install.cmd
if errorlevel 1 exit /b %errorlevel%
if not defined SST_NATIVE_THREADS set "SST_NATIVE_THREADS=16"
set "RES=%~2"
if "%RES%"=="" set "RES=600"
"%CD%\.venv\Scripts\python.exe" -m maxwell_sst.cli centerline "%~1" --resample %RES% --native-threads %SST_NATIVE_THREADS% --out 4_outputs_one
exit /b %ERRORLEVEL%
