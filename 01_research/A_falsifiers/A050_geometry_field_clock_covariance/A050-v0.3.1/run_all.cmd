@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.3.1-outputs"
set "WB=%~1"
echo ============================================================
echo A050 v0.3.1 Nonstationary Phase/Frequency Drift Diagnostic
echo DIAGNOSTIC BLIND RERUN -- parent v0.3.0 verdict frozen
echo ============================================================
call run_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat
set "OPENBLAS_NUM_THREADS=1"
set "OMP_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
set "NUMEXPR_NUM_THREADS=1"
python tools\preflight.py || exit /b 1
if defined WB (python tools\stage_external_geometry.py --workbench-root "%WB%" --config config/default.json) else (python tools\stage_external_geometry.py --config config/default.json)
if errorlevel 1 exit /b 1
python tools\preflight.py || exit /b 1
python tools\audit_blind.py || exit /b 1
python -m pytest -q || exit /b 1
python -m sst_gfcc_blind.cli --config config/default.json --out "%OUT%" || exit /b 1
python tools\make_report.py "%OUT%" || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\*' -DestinationPath '..\SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.3.1-outputs_BLIND.zip'"
echo.
echo v0.3.1 DIAGNOSTIC campaign complete. Parent v0.3.0 verdict remains frozen. Run run_reveal.cmd only after freezing the BLIND output archive/hash.
endlocal
