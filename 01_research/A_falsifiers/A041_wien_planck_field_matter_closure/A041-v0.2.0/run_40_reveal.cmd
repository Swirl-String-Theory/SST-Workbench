@echo off
setlocal
set OUT=%~1
if "%OUT%"=="" if exist outputs\LAST_OUT.txt set /p OUT=<outputs\LAST_OUT.txt
if "%OUT%"=="" (
  echo ERROR: Missing output directory.
  exit /b 2
)
call .venv\Scripts\activate.bat || exit /b 1
python -m sst_wp.action_reveal "%OUT%\BLIND_RESULTS.json" "%OUT%\BLIND_SEAL.json" "%OUT%\BLIND_INPUT.csv" --private-dir private_reveal_keys --out "%OUT%\REVEALED_RESULTS.json" || exit /b 1
python -m sst_wp.report "%OUT%\REVEALED_RESULTS.json" --out "%OUT%\REPORT_REVEALED.md" --title "Wien-Planck SST v0.2.0 REVEALED report" || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\*' -DestinationPath '%OUT%\Wien_Planck_v0.2.0_REVEALED.zip'" || exit /b 1
endlocal
