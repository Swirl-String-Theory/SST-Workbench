@echo off
setlocal
set OUT=%~1
if "%OUT%"=="" set OUT=outputs\basic
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json
echo ============================================================
echo SST Trefoil Dynamic Seed Qualification v0.2.0
echo Resume from S32 using an already completed S10-S30 output tree
echo Output: %OUT%
echo Config: %CFG%
echo ============================================================
call run_00_setup.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_02_selftest.cmd || exit /b 1
call run_32_temporal.cmd "%OUT%" "%CFG%" || exit /b 1
call run_35_core.cmd "%OUT%" "%CFG%" || exit /b 1
call run_37_mesh_gauge.cmd "%OUT%" "%CFG%" || exit /b 1
call run_40_long.cmd "%OUT%" "%CFG%" || exit /b 1
call run_50_rpo.cmd "%OUT%" "%CFG%" || exit /b 1
call run_60_mechanism.cmd "%OUT%" "%CFG%" || exit /b 1
call run_70_reveal.cmd "%OUT%" || exit /b 1
