@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call config\paths.cmd
if not defined KK_PY set "KK_PY=%CD%\.venv\Scripts\python.exe"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=basic"
set "THREADS=%~2"
if "%THREADS%"=="" set "THREADS=16"
set "KNOTS=%~3"
if "%KNOTS%"=="" set "KNOTS=%SST_KNOTS_DIR%"
if /I "%MODE%"=="basic" set "CFG=config\basic.json"
if /I "%MODE%"=="extended" set "CFG=config\extended.json"
if not defined CFG (
  echo Usage: run_30_custom.cmd basic^|extended [threads] [knots_dir]
  exit /b 2
)
"%KK_PY%" run_campaign.py --config "%CFG%" --knots "%KNOTS%" --threads %THREADS% --require-native
exit /b %errorlevel%
