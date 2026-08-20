@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_extended_prepare.cmd || exit /b 1
call run_extended_blind.cmd || exit /b 1
call run_extended_reveal.cmd || exit /b 1
call run_pressure_law_prepare.cmd || exit /b 1
call run_pressure_law_blind.cmd || exit /b 1
call run_pressure_law_reveal.cmd || exit /b 1
call run_far_field_prepare.cmd || exit /b 1
call run_far_field_blind.cmd || exit /b 1
call run_far_field_reveal.cmd || exit /b 1
call run_triple_gear_prepare.cmd || exit /b 1
call run_triple_gear_blind.cmd || exit /b 1
call run_triple_gear_reveal.cmd || exit /b 1
echo [SST-TH v0.2.0] full confirmatory core complete.
echo Optional long discovery scan: run_all_stability_islands.cmd
exit /b 0
