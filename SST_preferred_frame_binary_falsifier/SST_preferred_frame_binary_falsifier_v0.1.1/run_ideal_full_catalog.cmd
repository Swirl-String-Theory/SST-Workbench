@echo off
setlocal
cd /d "%~dp0"
python run_ideal_database.py --all-knots --all-links --no-linking --out-dir audit_out\ideal_full_catalog
