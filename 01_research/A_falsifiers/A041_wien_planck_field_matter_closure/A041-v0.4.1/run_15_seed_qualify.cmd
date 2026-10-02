@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=private_reveal_keys\funnel_cpu_candidates
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.1-outputs"
set "PRIV=private_reveal_keys"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist "%DATA%" (echo ERROR: Run run_12_gpu_funnel.cmd first. & popd & exit /b 2)
if not exist "%PRIV%\GPU_FUNNEL_PRIVATE.json" (echo ERROR: Missing GPU funnel private map. & popd & exit /b 2)
if not exist "%OUTROOT%\qualification" mkdir "%OUTROOT%\qualification"
"%PY%" -m sst_wp.seed_qualification "%DATA%" --config "%CFG%" --out "%OUTROOT%\qualification\QUALIFICATION_PUBLIC.json" --selection "%PRIV%\SELECTED_INPUTS.json" --private-dir "%PRIV%" --candidate-map "%PRIV%\GPU_FUNNEL_PRIVATE.json" || exit /b 1
popd
endlocal
