@echo off
call "%~dp0run_radial_convergence_prepare.cmd" || exit /b 1
call "%~dp0run_radial_convergence_blind.cmd" || exit /b 1
call "%~dp0run_radial_convergence_reveal.cmd" || exit /b 1
