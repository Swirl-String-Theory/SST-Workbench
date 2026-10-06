@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.4.0-outputs"
set "WB=%~1"
echo ============================================================
echo A050 v0.4.0 Phase-Reversal Mechanism Discrimination
echo FRESH-HOLDOUT BLIND REPLICATION -- parent results frozen
echo ============================================================
call run_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat
set "OPENBLAS_NUM_THREADS=1"
set "OMP_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
set "NUMEXPR_NUM_THREADS=1"
python tools\preflight.py --config config/default.json --seal-only || exit /b 1
if defined WB (python tools\stage_external_geometry.py --workbench-root "%WB%" --config config/default.json) else (python tools\stage_external_geometry.py --config config/default.json)
if errorlevel 1 exit /b 1
python tools\stage_v040_holdouts.py --config config/default.json || exit /b 1
python tools\preflight.py --config config/default.json || exit /b 1
python tools\audit_blind.py || exit /b 1
python -m pytest -q || exit /b 1
python -m sst_gfcc_blind.mechanism_campaign --config config/default.json --out "%OUT%" || exit /b 1
python tools\make_report.py "%OUT%" || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\*' -DestinationPath '..\SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.4.0-outputs_BLIND.zip'"
echo.
echo v0.4.0 mechanism campaign complete. Parent v0.3.0/v0.3.2 results remain frozen.
endlocal
