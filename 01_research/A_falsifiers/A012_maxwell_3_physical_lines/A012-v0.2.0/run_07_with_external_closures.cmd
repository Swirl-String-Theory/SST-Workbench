@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
if "%~1"=="" goto usage
set "RM=%~1"
set "STORAGE=%~2"
if "%STORAGE%"=="" (
  "%PY%" -m sst_maxwell3_blind.cli run --profile extended --knots "%KNOTS_DIR%" --threads %SST_NATIVE_THREADS% --reduced-momentum "%RM%"
) else (
  "%PY%" -m sst_maxwell3_blind.cli run --profile extended --knots "%KNOTS_DIR%" --threads %SST_NATIVE_THREADS% --reduced-momentum "%RM%" --storage "%STORAGE%"
)
exit /b %errorlevel%
:usage
echo Usage: run_07_with_external_closures.cmd reduced_momentum.csv [storage_current.npz]
exit /b 2
