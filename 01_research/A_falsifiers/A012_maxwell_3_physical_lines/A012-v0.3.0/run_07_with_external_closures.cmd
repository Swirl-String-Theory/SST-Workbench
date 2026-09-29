@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
if "%~1"=="" goto usage
if defined SST_WORKBENCH_ROOT (
  if "%~2"=="" (
    "%PY%" -m sst_maxwell3_blind.cli run --profile basic --workbench "%SST_WORKBENCH_ROOT%" --threads %SST_NATIVE_THREADS% --reduced-momentum "%~1"
  ) else (
    "%PY%" -m sst_maxwell3_blind.cli run --profile basic --workbench "%SST_WORKBENCH_ROOT%" --threads %SST_NATIVE_THREADS% --reduced-momentum "%~1" --storage "%~2"
  )
) else (
  if "%~2"=="" (
    "%PY%" -m sst_maxwell3_blind.cli run --profile basic --threads %SST_NATIVE_THREADS% --reduced-momentum "%~1"
  ) else (
    "%PY%" -m sst_maxwell3_blind.cli run --profile basic --threads %SST_NATIVE_THREADS% --reduced-momentum "%~1" --storage "%~2"
  )
)
exit /b %errorlevel%
:usage
echo Usage: run_07_with_external_closures.cmd reduced_momentum.csv [storage_directory]
exit /b 2
