@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "PY=.venv\Scripts\python.exe"
set "DATA=private_reveal_keys\funnel_cpu_candidates"
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.1-outputs"
if not exist "%DATA%" (echo ERROR: Run funnel first. & popd & exit /b 2)
"%PY%" -m sst_wp.inventory "%DATA%" --out private_reveal_keys\STAGE_C_INVENTORY_PRIVATE.json --public-out "%OUTROOT%\STAGE_C_INVENTORY_PUBLIC.json" || exit /b 1
popd
endlocal
