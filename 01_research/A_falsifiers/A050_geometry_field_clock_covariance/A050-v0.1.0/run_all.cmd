@echo off
setlocal
set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.1.0-outputs"
echo ============================================================
echo SST Geometry Field Clock Covariance Blind Falsifier v0.1.0
echo Python reference campaign - dimensionless blind path
echo ============================================================
call run_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat
python -m sst_gfcc_blind.cli --config config/default.json --out "%OUT%" || exit /b 1
python tools\audit_blind.py sst_gfcc_blind reveal\audit_policy.json || exit /b 1
python tools\audit_blind.py config reveal\audit_policy.json || exit /b 1
python tools\audit_blind.py "%OUT%" reveal\audit_policy.json || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\*' -DestinationPath '..\SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.1.0-outputs_BLIND.zip'"
echo Blind run complete.
endlocal
