@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\KnotPlot\knots\final
set OUT=outputs\basic
set CFG=config\basic.json
echo ============================================================
echo SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.2.0
echo BASIC full staged chain
echo Dataset: %DATA%
echo S10 source atlas ^> S20 rolling ^> S25 refine ^> S30 spatial
echo ^> S32 temporal ^> S35 core ^> S37 mesh gauge ^> S40 long
echo ^> S50 projected Floquet ^> S60 mechanism ^> S70 reveal
echo ============================================================
call run_00_setup.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_02_selftest.cmd || exit /b 1
call run_10_prepare.cmd "%DATA%" "%OUT%" "%CFG%" || exit /b 1
call run_20_early.cmd "%OUT%" "%CFG%" || exit /b 1
call run_25_refine.cmd "%OUT%" "%CFG%" || exit /b 1
call run_30_resolution.cmd "%OUT%" "%CFG%" || exit /b 1
call run_32_temporal.cmd "%OUT%" "%CFG%" || exit /b 1
call run_35_core.cmd "%OUT%" "%CFG%" || exit /b 1
call run_37_mesh_gauge.cmd "%OUT%" "%CFG%" || exit /b 1
call run_40_long.cmd "%OUT%" "%CFG%" || exit /b 1
call run_50_rpo.cmd "%OUT%" "%CFG%" || exit /b 1
call run_60_mechanism.cmd "%OUT%" "%CFG%" || exit /b 1
call run_70_reveal.cmd "%OUT%" || exit /b 1
echo ============================================================
echo BASIC chain complete.
echo Inspect: %OUT%\BLIND_CHAIN_SUMMARY.json
echo          %OUT%\REVEAL_SUMMARY.json
echo ============================================================
