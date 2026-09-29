@echo off
setlocal
set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.3-outputs"
echo ============================================================
echo A050 v0.2.3 Local Basin / Perturbation-Sensitivity Map
echo POST-CONFIRMATORY DIAGNOSTIC -- v0.2.2 verdict remains locked
echo 72 nonzero trajectories + baseline; resumable; deterministic single-worker default
echo ============================================================
call run_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat
set "OPENBLAS_NUM_THREADS=1"
set "OMP_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
set "NUMEXPR_NUM_THREADS=1"
python tools\preflight.py || exit /b 1
python -m pytest -q || exit /b 1
python -m sst_gfcc_blind.cli --config config/default.json --out "%OUT%" || exit /b 1
python tools\make_report.py "%OUT%" || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\*' -DestinationPath '..\SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.3-outputs_DIAGNOSTIC.zip'"
echo.
echo v0.2.3 diagnostic campaign complete.
echo Parent v0.2.2 verdict was NOT superseded.
endlocal
