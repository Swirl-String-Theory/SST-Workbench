@echo off
setlocal
python -m sst_counterpulley.build_ext_if_needed --strict
if errorlevel 1 exit /b %errorlevel%
python run_rpo_search.py --scan --out-dir rpo_out
exit /b %errorlevel%
