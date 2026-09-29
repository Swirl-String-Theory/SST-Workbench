@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
echo ============================================================
echo 3_MAXWELL v0.3.0 - CERTIFICATION blind PKLSA campaign
echo ALL admissible non-duplicate carriers; expensive.
echo ============================================================
if defined SST_WORKBENCH_ROOT (
  "%PY%" -m sst_maxwell3_blind.cli run --profile certification --workbench "%SST_WORKBENCH_ROOT%" --threads %SST_NATIVE_THREADS%
) else (
  "%PY%" -m sst_maxwell3_blind.cli run --profile certification --threads %SST_NATIVE_THREADS%
)
exit /b %errorlevel%
