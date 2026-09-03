@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=datasets\SST_Parametric_Trefoil_Seed_Atlas_v1.0.0\candidates
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs"
set "PRIV=private_reveal_keys"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist "%OUTROOT%" mkdir "%OUTROOT%"
if not exist "%PRIV%" mkdir "%PRIV%"
"%PY%" -m sst_wp.inventory "%DATA%" --out "%PRIV%\DATASET_INVENTORY_PRIVATE.json" --public-out "%OUTROOT%\DATASET_INVENTORY_PUBLIC.json" --n 96 || exit /b 1
popd
endlocal
