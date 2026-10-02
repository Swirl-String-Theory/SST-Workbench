@echo off
setlocal
python -m sst_counterpulley.build_ext_if_needed --strict
if errorlevel 1 exit /b %errorlevel%
python run_true_floquet.py --out true_floquet.json
exit /b %errorlevel%
