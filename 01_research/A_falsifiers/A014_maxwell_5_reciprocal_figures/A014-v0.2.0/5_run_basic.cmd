@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call 5_env.cmd
if errorlevel 1 exit /b %errorlevel%
set "THREADS=%NUMBER_OF_PROCESSORS%"
if "%THREADS%"=="" set "THREADS=8"
if not "%~1"=="" set "THREADS=%~1"
set "KNOTS=%M5_KNOTS_DEFAULT%"
if not "%~2"=="" set "KNOTS=%~2"
if not exist "%KNOTS%\knot_3.1_final.txt" (
  echo ERROR: expected shared-final knot dataset not found in "%KNOTS%"
  exit /b 2
)
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%I"
set "OUT=%CD%\outputs_basic_%TS%"
mkdir "%OUT%" >nul 2>nul
echo ============================================================
echo 5_Maxwell v0.2.0 BASIC - %THREADS% native threads
echo knots: "%KNOTS%"
echo out:   "%OUT%"
echo ============================================================
"%M5_PY%" tools\5_make_manifest.py --input-dir "%KNOTS%" --preset basic --config config\presets\basic.json --out "%OUT%\datasets.private.json" || exit /b 3
"%M5_PY%" python\prepare_blind.py "%OUT%\datasets.private.json" --out "%OUT%\blind_campaign" --private-key "%OUT%\private_blind_key.json" || exit /b 4
"%M5_PY%" python\run_blind.py "%OUT%\blind_campaign" --threads %THREADS% --require-native || exit /b 5
"%M5_PY%" python\unblind.py "%OUT%\blind_campaign\results" "%OUT%\private_blind_key.json" --out "%OUT%\unblinded_summary.json" --csv "%OUT%\unblinded_summary.csv" || exit /b 6
"%M5_PY%" tools\5_summarize.py "%OUT%\unblinded_summary.json" --out "%OUT%\REPORT.md" || exit /b 7
echo.
echo [5_Maxwell] BASIC COMPLETE: "%OUT%"
exit /b 0
