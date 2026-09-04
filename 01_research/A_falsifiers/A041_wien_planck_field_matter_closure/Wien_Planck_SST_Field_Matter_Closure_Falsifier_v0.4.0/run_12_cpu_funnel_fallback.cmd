@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set CFG=%~1
if "%CFG%"=="" set CFG=config\basic.json
set "PY=.venv\Scripts\python.exe"
set "ATLAS=datasets\SST_Parametric_Knot_Link_Seed_Atlas_v0.1.0"
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.0-outputs"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
echo WARNING: CPU fallback screens all 2352 candidates and may be substantially slower than SYCL GPU.
"%PY%" -m sst_wp.gpu_funnel "%ATLAS%" --config "%CFG%" --out-root "%OUTROOT%" --private-dir private_reveal_keys --backend cpu || exit /b 1
popd
endlocal
