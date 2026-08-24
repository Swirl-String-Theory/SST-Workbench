@echo off
rem Safe complete default: install + backend + basic relaxed-knot workflow +
rem Boltzmann/Verlinde self-tests. Extended 1200-point run stays separate.
call "%~dp0run_00_install.cmd" || exit /b 1
call "%~dp0run_01_check_backend.cmd" || exit /b 1
call "%~dp0run_10_basic.cmd" || exit /b 1
call "%~dp0run_40_bv_demo_pass.cmd" || exit /b 1
call "%~dp0run_41_bv_demo_fail.cmd" || exit /b 1
exit /b 0
