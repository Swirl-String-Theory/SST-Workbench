@echo off
setlocal
cd /d "%~dp0"
python upgrade_calibration_json.py generate --plan independent_calibration_plan_v0.1.json --out calibration_v2_draft.json --results-template calibration_results_template.csv
if errorlevel 1 goto :error
echo.
echo Created calibration_v2_draft.json and calibration_results_template.csv
pause
exit /b 0
:error
echo.
echo ERROR: calibration draft generation failed.
pause
exit /b 1
