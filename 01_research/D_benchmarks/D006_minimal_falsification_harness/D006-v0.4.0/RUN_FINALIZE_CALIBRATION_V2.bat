@echo off
setlocal
cd /d "%~dp0"
python upgrade_calibration_json.py finalize --draft calibration_v2_draft.json --results calibration_results_template.csv --out calibration_filled_v2.json
if errorlevel 1 goto :error
echo.
echo Created calibration_filled_v2.json
pause
exit /b 0
:error
echo.
echo ERROR: fill every required CSV result and provenance field first.
pause
exit /b 1
