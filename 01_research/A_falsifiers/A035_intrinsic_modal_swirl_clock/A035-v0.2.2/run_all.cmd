@echo off
setlocal
echo ============================================================
echo SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.2.2
echo BASIC seed-provenance + mesh-certified one-click chain
echo Relaxed:  ..\..\KnotPlot\knots\final
echo Fseries:  ..\..\KnotPlot\Knots_FourierSeries
echo Ideal:    ..\..\Ideal_Sources\Ideal.txt[.gz]
echo Links:    ..\..\Ideal_Sources\IdealLinks.txt[.gz]
echo Stage A:  T=24, matched topology comparison
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call run_provenance_scan.cmd || exit /b 1
call run_basic.cmd || exit /b 1
