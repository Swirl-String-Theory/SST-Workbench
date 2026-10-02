@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set OUT=%~1
if "%OUT%"=="" if exist outputs\LAST_OUT.txt set /p OUT=<outputs\LAST_OUT.txt
if "%OUT%"=="" (
  echo ERROR: Missing output directory.
  exit /b 2
)
set NORM=%~2
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
if "%NORM%"=="" (
  python -m sst_wp.action_reveal "%OUT%\BLIND_RESULTS.json" "%OUT%\BLIND_SEAL.json" "%OUT%\BLIND_INPUT.csv" --private-dir private_reveal_keys --out "%OUT%\REVEALED_RESULTS.json" || exit /b 1
) else (
  python -m sst_wp.action_reveal "%OUT%\BLIND_RESULTS.json" "%OUT%\BLIND_SEAL.json" "%OUT%\BLIND_INPUT.csv" --private-dir private_reveal_keys --normalization "%NORM%" --out "%OUT%\REVEALED_RESULTS.json" || exit /b 1
)
"%PY%" -m sst_wp.report "%OUT%\REVEALED_RESULTS.json" --out "%OUT%\REPORT_REVEALED.md" --title "Wien-Planck SST v0.2.2 REVEALED report" || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\*' -DestinationPath '%OUT%\Wien_Planck_v0.2.2_REVEALED.zip'" || exit /b 1
echo.
echo Optional independent normalization usage:
echo run_40_reveal.cmd "%OUT%" reveal_only\independent_normalization_TEMPLATE.json
popd
endlocal
