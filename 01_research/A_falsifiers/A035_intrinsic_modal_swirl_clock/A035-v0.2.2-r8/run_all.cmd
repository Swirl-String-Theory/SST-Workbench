@echo off
setlocal
echo ============================================================
echo SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.2.2.7
echo Library-selectable seed-provenance + mesh-certified chain
echo.
echo Usage:
echo   run_all.cmd --libraries=Fremlin,Gilbert,Katlas
echo   run_all.cmd --libraries=Fremlin,Gilbert,Katlas --min-carriers=2
echo   run_all.cmd --libraries=Gilbert,Katlas --min-carriers=2 --kind=links
echo   run_all.cmd --libraries=KnotPlot,Fremlin,Gilbert,Katlas
echo.
echo Fremlin: ..\..\Ideal_Fremlin_Fseries\fremlin
echo Gilbert: ..\..\Ideal_Sources
 echo Katlas:  ..\..\Katlas_Sources_v0.2.2_Outputs  (knots + links)
echo KnotPlot: ..\..\KnotPlot\knots\final  (only when selected)
echo Stage A: T=24 matched topology comparison
echo ============================================================
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
call run_provenance_scan.cmd %* || exit /b 1
call run_basic.cmd %* || exit /b 1
