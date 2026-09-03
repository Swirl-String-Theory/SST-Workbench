@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=datasets\SST_Parametric_Trefoil_Seed_Atlas_v1.0.0\candidates
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs"
set "PRIV=private_reveal_keys"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist "%OUTROOT%\qualification" mkdir "%OUTROOT%\qualification"
if not exist "%PRIV%" mkdir "%PRIV%"
"%PY%" -m sst_wp.seed_qualification "%DATA%" --config "%CFG%" --out "%OUTROOT%\qualification\QUALIFICATION_PUBLIC.json" --selection "%PRIV%\SELECTED_INPUTS.json" --private-dir "%PRIV%" || exit /b 1
popd
endlocal
