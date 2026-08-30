@echo off
setlocal
echo ============================================================
echo SST SC-II Intrinsic Modal Phase Swirl-Clock Blind Falsifier v0.1.1
echo Full-shape recurrence is NOT required.
echo Primary observable: monotone predictive natural modal phase phi(t).
echo.
echo Examples:
echo   run_all.cmd --libraries=Fremlin,Gilbert,Katlas --min-carriers=2
echo   run_all.cmd --libraries=Gilbert,Katlas --min-carriers=2 --kind=links
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call run_provenance_scan.cmd %* || exit /b 1
call run_basic.cmd %* || exit /b 1
