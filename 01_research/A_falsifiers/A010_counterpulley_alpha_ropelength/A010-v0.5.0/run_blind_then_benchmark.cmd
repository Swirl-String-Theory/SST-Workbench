@echo off
setlocal
python -m sst_counterpulley.build_ext_if_needed --strict
if errorlevel 1 exit /b %errorlevel%
python run_blind.py --out-dir audit_out_blind
if errorlevel 1 exit /b %errorlevel%
rem run_benchmark.py itself refuses to import the alpha module unless H18 is open.
python run_benchmark.py audit_out_blind\blind_audit_summary.json --out audit_out_blind\posthoc_alpha_benchmark.json
exit /b %errorlevel%
