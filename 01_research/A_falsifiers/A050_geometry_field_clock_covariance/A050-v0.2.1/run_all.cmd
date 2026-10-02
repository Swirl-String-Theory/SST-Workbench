@echo off
setlocal
set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.1-outputs"
echo ============================================================
echo SST Geometry Field Clock Covariance Blind Falsifier v0.2.1
echo Spatial + temporal-memory + transverse-mode + Floquet gates
echo ============================================================
call run_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat
python -m pytest -q || exit /b 1
python -m sst_gfcc_blind.cli --config config/default.json --out "%OUT%" || exit /b 1
python tools\audit_blind.py sst_gfcc_blind reveal\audit_policy.json || exit /b 1
python tools\audit_blind.py config reveal\audit_policy.json || exit /b 1
python tools\audit_blind.py "%OUT%" reveal\audit_policy.json || exit /b 1
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\*' -DestinationPath '..\SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.1-outputs_BLIND.zip'"
echo Blind run complete.
endlocal
