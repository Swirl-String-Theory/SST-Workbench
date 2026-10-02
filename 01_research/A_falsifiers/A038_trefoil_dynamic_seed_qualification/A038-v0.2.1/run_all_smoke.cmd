@echo off
setlocal
set DATA=%~1
if "%DATA%"=="" set DATA=..\..\Knot_Geometry_Library\SST_Knot_Geometry_Library_v0.1.1\outputs\seed_suite
set OUT=outputs\workflow_smoke
set CFG=config\workflow_smoke.json
echo ============================================================
echo SST Trefoil Mega Falsifier v0.2.1 - WORKFLOW SMOKE ONLY
echo This profile cannot emit an SST physics PASS.
echo Dataset: %DATA%
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
echo Workflow smoke complete. Physics verdict must be NOT_APPLICABLE_WORKFLOW_VALIDATION.
