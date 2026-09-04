@echo off
setlocal
cd /d "%~dp0"

if not exist calibration_filled.json (
  echo Missing calibration_filled.json
  echo Copy calibration_template.json and replace all placeholders first.
  pause
  exit /b 1
)

python sst_minimal_falsification.py audit ^
  --calibration calibration_filled.json ^
  --geometry gilbert_trefoil_features.json ^
  --out falsification_report.json ^
  --abs-tol 0.001
if errorlevel 1 goto :error

python sst_minimal_falsification.py batch-predict ^
  --calibration calibration_filled.json ^
  --batch gilbert_feature_batch.json ^
  --out cross_knot_predictions.json
if errorlevel 1 goto :error

echo.
echo Falsification audit and frozen cross-knot predictions completed.
pause
exit /b 0

:error
echo.
echo ERROR: audit failed.
pause
exit /b 1
