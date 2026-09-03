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
python -m sst_wp.action_prepare "%OUT%\raw_observations.csv" --out-dir "%OUT%" --private-dir private_reveal_keys --quarantine-raw || exit /b 1
python -m sst_wp.action_analyze "%OUT%\BLIND_INPUT.csv" --config "%CFG%" --out "%OUT%\BLIND_RESULTS.json" || exit /b 1
python -m sst_wp.report "%OUT%\BLIND_RESULTS.json" --out "%OUT%\REPORT_BLIND.md" --title "Wien-Planck SST v0.2.0 BLIND report" || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\campaign.json','%OUT%\BLIND_INPUT.csv','%OUT%\BLIND_SEAL.json','%OUT%\BLIND_RESULTS.json','%OUT%\REPORT_BLIND.md' -DestinationPath '%OUT%\Wien_Planck_v0.2.0_BLIND.zip'" || exit /b 1
echo BLIND complete. Raw identities were quarantined under private_reveal_keys.
echo Read %OUT%\REPORT_BLIND.md before reveal.
endlocal
