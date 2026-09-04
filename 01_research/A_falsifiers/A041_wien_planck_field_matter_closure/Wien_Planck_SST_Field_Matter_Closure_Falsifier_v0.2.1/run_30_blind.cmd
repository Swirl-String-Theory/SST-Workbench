@echo off
setlocal
set OUT=%~1
if "%OUT%"=="" if exist outputs\LAST_OUT.txt set /p OUT=<outputs\LAST_OUT.txt
if "%OUT%"=="" (
  echo ERROR: Missing output directory.
  exit /b 2
)
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
call .venv\Scripts\activate.bat || exit /b 1
python -m sst_wp.blind_guard || exit /b 1
if exist outputs\BLIND_CODE_AUDIT.json copy /Y outputs\BLIND_CODE_AUDIT.json "%OUT%\BLIND_CODE_AUDIT.json" >nul
python -m sst_wp.action_prepare "%OUT%\raw_observations.csv" --out-dir "%OUT%" --private-dir private_reveal_keys --quarantine-raw || exit /b 1
python -m sst_wp.action_analyze "%OUT%\BLIND_INPUT.csv" --config "%CFG%" --out "%OUT%\BLIND_RESULTS.json" || exit /b 1
python -m sst_wp.report "%OUT%\BLIND_RESULTS.json" --out "%OUT%\REPORT_BLIND.md" --title "Wien-Planck SST v0.2.1 STRICT DIMENSIONLESS BLIND report" || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\campaign.json','%OUT%\BLIND_CODE_AUDIT.json','%OUT%\BLIND_INPUT.csv','%OUT%\BLIND_SEAL.json','%OUT%\BLIND_RESULTS.json','%OUT%\REPORT_BLIND.md' -DestinationPath '%OUT%\Wien_Planck_v0.2.1_BLIND.zip'" || exit /b 1
echo BLIND complete. No SST canonical constants or SI scales were supplied to campaign/scorer.
echo Read %OUT%\REPORT_BLIND.md before any reveal.
endlocal
