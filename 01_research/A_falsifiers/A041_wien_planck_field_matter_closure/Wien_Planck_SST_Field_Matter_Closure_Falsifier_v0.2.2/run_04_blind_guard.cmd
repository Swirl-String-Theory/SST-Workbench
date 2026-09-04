@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist outputs mkdir outputs
"%PY%" -m sst_wp.blind_guard --out outputs\BLIND_CODE_AUDIT.json || exit /b 1
echo Blind constant/SI leakage guard: PASS
popd
endlocal
