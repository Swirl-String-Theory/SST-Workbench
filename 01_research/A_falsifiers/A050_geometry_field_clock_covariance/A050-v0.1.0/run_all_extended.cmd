@echo off
setlocal
set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.1.0-outputs_extended"
call run_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat
python -m sst_gfcc_blind.cli --config config/extended.json --out "%OUT%" || exit /b 1
python tools\audit_blind.py sst_gfcc_blind reveal\audit_policy.json || exit /b 1
python tools\audit_blind.py config reveal\audit_policy.json || exit /b 1
python tools\audit_blind.py "%OUT%" reveal\audit_policy.json || exit /b 1
endlocal
