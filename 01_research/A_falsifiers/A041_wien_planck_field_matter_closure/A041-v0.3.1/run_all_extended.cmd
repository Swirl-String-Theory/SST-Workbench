@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set DATA=%~1
if "%DATA%"=="" set DATA=datasets\SST_Parametric_Trefoil_Seed_Atlas_v1.0.0\candidates
call run_00_setup.cmd || exit /b 1
call run_01_build_native_clean.cmd || exit /b 1
call run_02_selftest.cmd || exit /b 1
call run_03_seal.cmd || exit /b 1
call run_04_blind_guard.cmd || exit /b 1
call run_10_inventory.cmd "%DATA%" || exit /b 1
call run_15_seed_qualify.cmd "%DATA%" config\extended.json || exit /b 1
call run_20_campaign.cmd "%DATA%" config\extended.json || exit /b 1
call run_30_blind.cmd "" config\extended.json || exit /b 1
echo ============================================================
echo v0.3.1 EXTENDED STRICT BLIND PTSA chain complete.
echo Default dataset: SST Parametric Trefoil Seed Atlas v1.0.0.
echo Reveal remains manual.
echo ============================================================
popd
endlocal
