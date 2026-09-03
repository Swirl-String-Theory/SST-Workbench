@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
call run_00_setup.cmd || exit /b 1
call run_01_build_native_clean.cmd || exit /b 1
call run_02_selftest.cmd || exit /b 1
call run_03_seal.cmd || exit /b 1
call run_04_blind_guard.cmd || exit /b 1
call run_10_inventory.cmd "%DATA%" || exit /b 1
call run_20_campaign.cmd "%DATA%" config\basic.json || exit /b 1
call run_30_blind.cmd "" config\basic.json || exit /b 1
echo ============================================================
echo v0.2.2 STRICT BLIND chain complete.
echo No SST canonical constants or SI scales were used by the action campaign/scorer.
echo Reveal and provenance audit are intentionally manual.
echo ============================================================
popd
endlocal
