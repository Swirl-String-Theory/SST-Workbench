@echo off
setlocal
cd /d "%~dp0"
python -m pytest -q tests || exit /b 1
python src\phaseclock.py --out outputs\PREFLIGHT_RESULTS.json || exit /b 1
if exist data\A064-v0.3.0_results.json (
 python src\phaseclock.py --a064 data\A064-v0.3.0_results.json --out outputs\PREFLIGHT_WITH_A064.json || exit /b 1
)
echo PRELIMINARY only: not an SST Framework v1.0.7 certified run.
