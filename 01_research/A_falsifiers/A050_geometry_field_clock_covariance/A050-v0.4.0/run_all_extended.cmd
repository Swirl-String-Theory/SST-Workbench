@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.4.0-outputs-extended"
set "WB=%~1"
echo A050 v0.4.0 EXTENDED mechanism replication -- non-primary
call run_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat
python tools\preflight.py --config config/extended.json --seal-only || exit /b 1
if defined WB (python tools\stage_external_geometry.py --workbench-root "%WB%" --config config/extended.json) else (python tools\stage_external_geometry.py --config config/extended.json)
if errorlevel 1 exit /b 1
python tools\stage_v040_holdouts.py --config config/extended.json || exit /b 1
python tools\preflight.py --config config/extended.json || exit /b 1
python tools\audit_blind.py || exit /b 1
python -m sst_gfcc_blind.mechanism_campaign --config config/extended.json --out "%OUT%" || exit /b 1
python tools\make_report.py "%OUT%" || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\*' -DestinationPath '..\SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.4.0-outputs_EXTENDED.zip'"
endlocal
