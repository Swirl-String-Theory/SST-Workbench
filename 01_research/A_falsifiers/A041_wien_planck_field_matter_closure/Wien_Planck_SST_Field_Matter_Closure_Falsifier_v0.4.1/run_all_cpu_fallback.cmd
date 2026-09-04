@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set CFG=config\basic.json
call run_00_setup.cmd || exit /b 1
call run_01_build_native_clean.cmd || exit /b 1
call run_02_selftest.cmd || exit /b 1
call run_03_seal.cmd || exit /b 1
call run_04_blind_guard.cmd || exit /b 1
call run_06_verify_pklsa.cmd || exit /b 1
call run_12_cpu_funnel_fallback.cmd "%CFG%" || exit /b 1
call run_13_inventory_staged.cmd || exit /b 1
call run_15_seed_qualify.cmd "" "%CFG%" || exit /b 1
call run_20_campaign.cmd "" "%CFG%" || exit /b 1
call run_30_blind.cmd "" "%CFG%" || exit /b 1
echo CPU-fallback v0.4.1 chain complete. GPU was not used.
popd
endlocal
