@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.3.0-outputs_EXTENDED"
set "WB=%~1"
echo ============================================================
echo A050 v0.3.0 PKLSA Real-Geometry Transfer + Source-Independence Gate
echo NON-PRIMARY HIGH-RESOLUTION REPLICATION -- frozen external source panel
echo ============================================================
call run_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat
set "OPENBLAS_NUM_THREADS=1"
set "OMP_NUM_THREADS=1"
set "MKL_NUM_THREADS=1"
set "NUMEXPR_NUM_THREADS=1"
python tools\preflight.py || exit /b 1
if defined WB (python tools\stage_external_geometry.py --workbench-root "%WB%" --config config/extended.json) else (python tools\stage_external_geometry.py --config config/extended.json)
if errorlevel 1 exit /b 1
python tools\preflight.py || exit /b 1
python tools\audit_blind.py || exit /b 1
python -m pytest -q || exit /b 1
python -m sst_gfcc_blind.cli --config config/extended.json --out "%OUT%" || exit /b 1
python tools\make_report.py "%OUT%" || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\*' -DestinationPath '..\SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.3.0-outputs_EXTENDED_BLIND.zip'"
echo.
echo v0.3.0 EXTENDED replication complete; it does not replace the primary verdict.
endlocal
