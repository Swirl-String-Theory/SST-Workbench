@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set CFG=%~1
if "%CFG%"=="" set CFG=config\basic.json
set "PY=.venv\Scripts\python.exe"
set "ATLAS=datasets\SST_Parametric_Knot_Link_Seed_Atlas_v0.1.0"
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.0-outputs"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist gpu\sycl_funnel_fp32.exe (echo ERROR: Run run_07_build_gpu.cmd first. & popd & exit /b 2)
"%PY%" -m sst_wp.gpu_funnel "%ATLAS%" --config "%CFG%" --out-root "%OUTROOT%" --private-dir private_reveal_keys --backend sycl --gpu-exe gpu\sycl_funnel_fp32.exe || exit /b 1
echo PKLSA GPU funnel complete. Stage-C identities remain private.
popd
endlocal
