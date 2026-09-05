@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set CFG=%~1
if "%CFG%"=="" set CFG=config\basic.json
set "PY=.venv\Scripts\python.exe"
set "ATLAS=datasets\SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1"
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.1-outputs"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist gpu\sycl_funnel_fp32.exe (echo ERROR: Run run_07_build_gpu.cmd first. & popd & exit /b 2)
if not exist "%OUTROOT%\gpu" mkdir "%OUTROOT%\gpu"
if not exist private_reveal_keys\gpu_parity_work mkdir private_reveal_keys\gpu_parity_work
"%PY%" -m sst_wp.gpu_parity "%ATLAS%" --config "%CFG%" --gpu-exe gpu\sycl_funnel_fp32.exe --out "%OUTROOT%\gpu\GPU_CPU_PARITY.json" --work private_reveal_keys\gpu_parity_work || exit /b 1
echo GPU-to-CPU screening parity: PASS
popd
endlocal
