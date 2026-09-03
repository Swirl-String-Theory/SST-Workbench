@echo off
setlocal EnableExtensions EnableDelayedExpansion
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=datasets\SST_Parametric_Trefoil_Seed_Atlas_v1.0.0\candidates
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
set OUT=%~3
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs"
if "%OUT%"=="" (
  for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
  set "OUT=!OUTROOT!\basic_!TS!"
)
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist private_reveal_keys\SELECTED_INPUTS.json (echo ERROR: Run run_15_seed_qualify.cmd first. & popd & exit /b 2)
"%PY%" -m sst_wp.campaign "%DATA%" --config "%CFG%" --selection private_reveal_keys\SELECTED_INPUTS.json --out "%OUT%" || exit /b 1
if not exist "%OUTROOT%" mkdir "%OUTROOT%"
echo %OUT%> "%OUTROOT%\LAST_OUT.txt"
popd
endlocal
