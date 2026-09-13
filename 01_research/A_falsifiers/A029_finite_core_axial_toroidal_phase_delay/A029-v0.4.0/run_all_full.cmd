@echo off
call "%~dp0run_00_install.cmd" || exit /b 1
call "%~dp0run_01_build_native.cmd" || exit /b 1
call "%~dp0run_tests.cmd" || exit /b 1
call "%~dp0run_all_basic.cmd" || exit /b 1
call "%~dp0run_all_extended.cmd" || exit /b 1
call "%~dp0run_all_swirl_clock_phase_discovery.cmd" || exit /b 1
call "%~dp0run_all_swirl_clock_m2_diagnostic.cmd" || exit /b 1
call "%~dp0run_all_swirl_clock_branch_map.cmd" || exit /b 1
call "%~dp0run_all_phase_resolution_stress.cmd" || exit /b 1
call "%~dp0run_all_profile_robustness.cmd" || exit /b 1
call "%~dp0run_all_core_radius.cmd" || exit /b 1
call "%~dp0run_all_chirality_sign.cmd" || exit /b 1
call "%~dp0run_all_radial_convergence.cmd" || exit /b 1
