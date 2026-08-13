@echo off
setlocal
python -m sst_counterpulley.build_ext_if_needed --strict
if errorlevel 1 exit /b %errorlevel%
python run_all_checks.py --quick --out-dir audit_out_quick
exit /b %errorlevel%
