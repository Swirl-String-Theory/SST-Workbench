@echo off
call "%~dp0run_swirl_clock_branch_map_prepare.cmd" || exit /b 1
call "%~dp0run_swirl_clock_branch_map_blind.cmd" || exit /b 1
call "%~dp0run_swirl_clock_branch_map_reveal.cmd" || exit /b 1
