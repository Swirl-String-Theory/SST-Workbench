@echo off
setlocal
cd /d "%~dp0"
set PY=python
%PY% -m sst_pf_binary_falsifier.build_ext_if_needed --force
if errorlevel 1 exit /b 1
%PY% run_ideal_database.py --knot-ids 3:1:1 --link-ids L2a1,L4a1,L6n1 --out-dir audit_out\ideal_quick
if errorlevel 1 exit /b 1
%PY% run_drift_scan.py --ideal-knot-id 3:1:1 --ideal-samples 96 --steps 2 --out-dir audit_out\drift_3_1_1
if errorlevel 1 exit /b 1
%PY% run_drift_scan.py --ideal-link-id L2a1 --ideal-samples 64 --steps 1 --out-dir audit_out\drift_L2a1
if errorlevel 1 exit /b 1
echo [SST] Ideal.txt / IdealLinks.txt quick audit PASS
