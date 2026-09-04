@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "PY=.venv\Scripts\python.exe"
set "ATLAS=datasets\SST_Parametric_Knot_Link_Seed_Atlas_v0.1.0"
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.0-outputs"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist "%OUTROOT%" mkdir "%OUTROOT%"
"%PY%" "%ATLAS%\tools\verify_atlas.py" || exit /b 1
"%PY%" -m sst_wp.pklsa_inventory "%ATLAS%" --out "%OUTROOT%\PKLSA_INVENTORY_PUBLIC.json" || exit /b 1
echo PKLSA 2352 / 49 scope: PASS
popd
endlocal
