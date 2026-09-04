@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "PY=.venv\Scripts\python.exe"
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.0-outputs"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist "%OUTROOT%" mkdir "%OUTROOT%"
"%PY%" -m sst_wp.blind_guard --out "%OUTROOT%\BLIND_CODE_AUDIT.json" || exit /b 1
echo Blind constant/SI leakage guard: PASS
popd
endlocal
