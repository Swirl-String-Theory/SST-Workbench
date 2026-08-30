@echo off
setlocal
echo ============================================================
echo SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.2.2
echo EXTENDED seed-provenance + mesh-certified chain
echo Stage A: T=36, >=6 cycles required
echo Then relaxed priority-trio N=64/96/128 resolution audit
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call run_provenance_scan.cmd || exit /b 1
call run_extended.cmd || exit /b 1
call run_resolution.cmd || exit /b 1
echo Resolution result: outputs\RESOLUTION_SUMMARY.json
