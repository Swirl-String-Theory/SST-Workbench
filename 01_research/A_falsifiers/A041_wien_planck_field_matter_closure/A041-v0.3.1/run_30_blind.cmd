@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "OUTROOT=Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs"
set OUT=%~1
if "%OUT%"=="" if exist "%OUTROOT%\LAST_OUT.txt" set /p OUT=<"%OUTROOT%\LAST_OUT.txt"
if "%OUT%"=="" (echo ERROR: Missing output directory. & popd & exit /b 2)
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
"%PY%" -m sst_wp.blind_guard || exit /b 1
if exist "%OUTROOT%\BLIND_CODE_AUDIT.json" copy /Y "%OUTROOT%\BLIND_CODE_AUDIT.json" "%OUT%\BLIND_CODE_AUDIT.json" >nul
"%PY%" -m sst_wp.action_prepare "%OUT%\raw_observations.csv" --out-dir "%OUT%" --private-dir private_reveal_keys --quarantine-raw || exit /b 1
"%PY%" -m sst_wp.action_analyze "%OUT%\BLIND_INPUT.csv" --config "%CFG%" --campaign "%OUT%\campaign.json" --out "%OUT%\BLIND_RESULTS.json" || exit /b 1
"%PY%" -m sst_wp.report "%OUT%\BLIND_RESULTS.json" --out "%OUT%\REPORT_BLIND.md" --title "Wien-Planck SST v0.3.1 PTSA STRICT DIMENSIONLESS BLIND report" || exit /b 1
"%PY%" -m sst_wp.archive_outputs "%OUTROOT%" --mode blind --dest "..\Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs_BLIND.zip" || exit /b 1
"%PY%" -m sst_wp.archive_outputs "%OUTROOT%" --mode blind --dest "..\Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs.zip" || exit /b 1
echo BLIND complete. Shareable archives created outside the project folder.
echo Private reveal keys were NOT included.
popd
endlocal
