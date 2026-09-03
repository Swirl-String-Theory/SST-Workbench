@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "PY=.venv\Scripts\python.exe"
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs\demo_controls"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if not exist "%OUTROOT%" mkdir "%OUTROOT%"
"%PY%" -m sst_wp.action_prepare demo\action_positive.csv --out-dir "%OUTROOT%\positive" --private-dir private_reveal_keys || exit /b 1
"%PY%" -m sst_wp.action_analyze "%OUTROOT%\positive\BLIND_INPUT.csv" --config config\basic.json --out "%OUTROOT%\positive\BLIND_RESULTS.json" || exit /b 1
"%PY%" -m sst_wp.action_prepare demo\action_classical.csv --out-dir "%OUTROOT%\classical" --private-dir private_reveal_keys || exit /b 1
"%PY%" -m sst_wp.action_analyze "%OUTROOT%\classical\BLIND_INPUT.csv" --config config\basic.json --out "%OUTROOT%\classical\BLIND_RESULTS.json" || exit /b 1
"%PY%" -m sst_wp.closure_analyze demo\closure_positive.csv --config config\basic.json --out "%OUTROOT%\closure_positive.json" || exit /b 1
"%PY%" -m sst_wp.closure_analyze demo\closure_negative.csv --config config\basic.json --out "%OUTROOT%\closure_negative.json" || exit /b 1
popd
endlocal
