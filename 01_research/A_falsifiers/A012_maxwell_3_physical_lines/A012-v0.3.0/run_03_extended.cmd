@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
echo ============================================================
echo 3_MAXWELL v0.3.0 - EXTENDED blind PKLSA-v0.3.x campaign
echo Full admitted topology scan, one provenance-clean carrier/topology
echo C++/OpenMP REQUIRED by profile
echo ============================================================
if defined SST_WORKBENCH_ROOT (
  "%PY%" -m sst_maxwell3_blind.cli run --profile extended --workbench "%SST_WORKBENCH_ROOT%" --threads %SST_NATIVE_THREADS%
) else (
  "%PY%" -m sst_maxwell3_blind.cli run --profile extended --threads %SST_NATIVE_THREADS%
)
exit /b %errorlevel%
