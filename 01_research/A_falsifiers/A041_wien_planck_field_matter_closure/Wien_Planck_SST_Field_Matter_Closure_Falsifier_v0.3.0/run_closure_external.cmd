@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
if "%~1"=="" (echo Usage: run_closure_external.cmd ^<closure.csv^> & popd & exit /b 2)
set "PY=.venv\Scripts\python.exe"
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist "%OUTROOT%" mkdir "%OUTROOT%"
"%PY%" -m sst_wp.closure_analyze "%~1" --config config\basic.json --out "%OUTROOT%\closure_external.json" || exit /b 1
popd
endlocal
