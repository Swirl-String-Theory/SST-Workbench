@echo off
setlocal
python -m sst_counterpulley.build_ext_if_needed --strict
if errorlevel 1 exit /b %errorlevel%
python run_all_checks.py --out-dir audit_out_full
exit /b %errorlevel%
