@echo off
setlocal
echo ============================================================
echo SST SC-IIb Frozen Modal-Pair/Subspace Phase-Clock v0.1.0
echo EXTENDED: T=36, >=6 wraps, mesh gauge + N=64/96/128 audit
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call run_provenance_scan.cmd %* || exit /b 1
call run_extended.cmd %* || exit /b 1
call run_resolution.cmd || exit /b 1
echo Resolution result: outputs\RESOLUTION_SUMMARY.json
