@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call config\paths.cmd
if not defined KK_PY set "KK_PY=%CD%\.venv\Scripts\python.exe"
set "THREADS=%~1"
if "%THREADS%"=="" set "THREADS=16"
set "KNOTS=%~2"
if "%KNOTS%"=="" set "KNOTS=%SST_KNOTS_DIR%"
if not exist "%KNOTS%" (
  echo [KK-SST] Knot directory not found: "%KNOTS%"
  echo [KK-SST] Pass it explicitly: run_10_basic.cmd 16 D:\path\to\KnotPlot\knots\final
  exit /b 2
)
"%KK_PY%" run_campaign.py --config config\basic.json --knots "%KNOTS%" --threads %THREADS% --require-native
exit /b %errorlevel%
