@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.0-outputs"
set OUT=%~1
if "%OUT%"=="" if exist "%OUTROOT%\LAST_OUT.txt" set /p OUT=<"%OUTROOT%\LAST_OUT.txt"
if "%OUT%"=="" (echo ERROR: Missing output directory. & popd & exit /b 2)
set NORM=%~2
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if "%NORM%"=="" (
  "%PY%" -m sst_wp.action_reveal "%OUT%\BLIND_RESULTS.json" "%OUT%\BLIND_SEAL.json" "%OUT%\BLIND_INPUT.csv" --private-dir private_reveal_keys --out "%OUT%\REVEALED_RESULTS.json" || exit /b 1
) else (
  "%PY%" -m sst_wp.action_reveal "%OUT%\BLIND_RESULTS.json" "%OUT%\BLIND_SEAL.json" "%OUT%\BLIND_INPUT.csv" --private-dir private_reveal_keys --normalization "%NORM%" --out "%OUT%\REVEALED_RESULTS.json" || exit /b 1
)
"%PY%" -m sst_wp.report "%OUT%\REVEALED_RESULTS.json" --out "%OUT%\REPORT_REVEALED.md" --title "Wien-Planck SST v0.4.0 PKLSA-2352 REVEALED report" || exit /b 1
"%PY%" -m sst_wp.archive_outputs "%OUTROOT%" --mode revealed --dest "..\Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.0-outputs_REVEALED.zip" || exit /b 1
echo REVEALED archive created. The default Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.4.0-outputs.zip remains blind-safe.
popd
endlocal
