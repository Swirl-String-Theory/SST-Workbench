@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd
if errorlevel 1 exit /b %errorlevel%
if not defined SST_NATIVE_THREADS set "SST_NATIVE_THREADS=16"
set "KNOT_DIR=%~1"
if "%KNOT_DIR%"=="" set "KNOT_DIR=%~dp0..\..\KnotPlot\knots\final"
if not exist "%KNOT_DIR%" (
  echo [4_SST] ERROR: knot directory not found: "%KNOT_DIR%"
  exit /b 2
)
call run_native_preflight.cmd
if errorlevel 1 exit /b %errorlevel%
echo [4_SST] EXTENDED run: N=300,600,1200; T05 at N=600.
echo [4_SST] Knots: "%KNOT_DIR%"
echo [4_SST] Native threads: %SST_NATIVE_THREADS%
"%CD%\.venv\Scripts\python.exe" -m maxwell_sst.cli batch --input "%KNOT_DIR%" --preset extended --native-threads %SST_NATIVE_THREADS%
exit /b %ERRORLEVEL%
