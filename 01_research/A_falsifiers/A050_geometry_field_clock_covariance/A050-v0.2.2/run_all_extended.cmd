@echo off
setlocal
set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.2-outputs_extended"
call run_setup.cmd || exit /b 1
call .venv\Scripts\activate.bat
python tools\preflight.py || exit /b 1
python -m pytest -q || exit /b 1
python -m sst_gfcc_blind.cli --config config/extended.json --out "%OUT%" || exit /b 1
python tools\make_report.py "%OUT%" || exit /b 1
python tools\audit_blind.py sst_gfcc_blind reveal\audit_policy.json || exit /b 1
python tools\audit_blind.py config reveal\audit_policy.json || exit /b 1
python tools\audit_blind.py data reveal\audit_policy.json || exit /b 1
python tools\audit_blind.py "%OUT%" reveal\audit_policy.json || exit /b 1
endlocal
