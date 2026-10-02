@echo off
setlocal EnableExtensions EnableDelayedExpansion
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=private_reveal_keys\funnel_cpu_candidates
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
set OUT=%~3
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.1-outputs"
for %%F in ("%CFG%") do set "PROFILE=%%~nF"
if "%OUT%"=="" (
  for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
  set "OUT=!OUTROOT!\!PROFILE!_!TS!"
)
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist private_reveal_keys\SELECTED_INPUTS.json (echo ERROR: Run run_15_seed_qualify.cmd first. & popd & exit /b 2)
"%PY%" -m sst_wp.campaign "%DATA%" --config "%CFG%" --selection private_reveal_keys\SELECTED_INPUTS.json --funnel-public "%OUTROOT%\funnel\GPU_FUNNEL_PUBLIC.json" --gpu-parity "%OUTROOT%\gpu\GPU_CPU_PARITY.json" --out "%OUT%" || exit /b 1
if not exist "%OUTROOT%" mkdir "%OUTROOT%"
echo %OUT%> "%OUTROOT%\LAST_OUT.txt"
popd
endlocal
