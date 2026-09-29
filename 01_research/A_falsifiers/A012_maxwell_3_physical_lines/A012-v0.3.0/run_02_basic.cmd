@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
echo ============================================================
echo 3_MAXWELL v0.3.0 - BASIC blind PKLSA campaign
echo M1-M3: source-native PKLSA stress anchors
echo M6: Maxwell-Hopf topological circulation
echo M7: mutual-helicity/linking when multicomponent evidence exists
echo ============================================================
if defined SST_WORKBENCH_ROOT (
  "%PY%" -m sst_maxwell3_blind.cli run --profile basic --workbench "%SST_WORKBENCH_ROOT%" --threads %SST_NATIVE_THREADS%
) else (
  "%PY%" -m sst_maxwell3_blind.cli run --profile basic --threads %SST_NATIVE_THREADS%
)
exit /b %errorlevel%
