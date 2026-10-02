@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
set "PROFILE=%~1"
if "%PROFILE%"=="" set "PROFILE=basic"
echo ============================================================
echo 3_MAXWELL v0.3.0 - PKLSA preflight [%PROFILE%]
echo Workbench: %SST_WORKBENCH_ROOT%
echo Threads: %SST_NATIVE_THREADS%
echo ============================================================
if defined SST_WORKBENCH_ROOT (
  "%PY%" -m sst_maxwell3_blind.cli preflight --profile "%PROFILE%" --workbench "%SST_WORKBENCH_ROOT%" --threads %SST_NATIVE_THREADS% --force-build
) else (
  "%PY%" -m sst_maxwell3_blind.cli preflight --profile "%PROFILE%" --threads %SST_NATIVE_THREADS% --force-build
)
exit /b %errorlevel%
